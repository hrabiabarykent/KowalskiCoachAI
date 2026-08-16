import math
from typing import Dict, Any, Tuple, List, Optional
import json
from app.domain.prompt_builders import build_ai_wellness_evaluation_prompt
from app.integrations.llm_client import GeminiClient
from pydantic import BaseModel

class WellnessEvaluationResult(BaseModel):
    needs_revision: bool
    reason: str
    forced_decision: Optional[str] = None
    overrides: List[str] = []

def check_tactical_overrides(
    wellness_list: List[Dict[str, Any]],
    today_str: Optional[str] = None,
    compliance: Optional[Dict[str, Any]] = None
) -> Tuple[Dict[str, Any], float, List[str], Optional[str]]:
    """
    Wylicza rolowane 30-dniowe HRV Baseline z odchyleniem standardowym (SD),
    wykrywa spadek poniżej dolnego progu normy (Baseline - 1.0*SD przy spadku >= 8% lub spadek > 15%)
    oraz skok RHR (>= +5 bpm).
    Zwraca: (latest_wellness, hrv_drop, overrides_list, forced_decision)
    """
    if not wellness_list:
        return {}, 0.0, [], None

    sorted_wellness = sorted(
        [w for w in wellness_list if isinstance(w, dict)],
        key=lambda x: str(x.get("date") or x.get("id") or "")
    )
    if not sorted_wellness:
        return {}, 0.0, [], None

    if today_str:
        wellness_today = next(
            (w for w in sorted_wellness if str(w.get("date") or w.get("id") or "") == today_str),
            None
        )
        latest_wellness = wellness_today or sorted_wellness[-1]
    else:
        latest_wellness = sorted_wellness[-1]

    target_date = str(latest_wellness.get("date") or latest_wellness.get("id") or "")

    prior_hrvs = [
        float(w["hrv"]) for w in sorted_wellness
        if w.get("hrv") is not None and float(w["hrv"]) > 0
        and str(w.get("date") or w.get("id") or "") < target_date
    ]

    if len(prior_hrvs) >= 3:
        hrv_baseline = sum(prior_hrvs) / len(prior_hrvs)
        variance = sum((x - hrv_baseline) ** 2 for x in prior_hrvs) / len(prior_hrvs)
        hrv_sd = math.sqrt(variance)
        hrv_lower_threshold = hrv_baseline - (1.0 * hrv_sd)
    else:
        hrv_baseline = float(latest_wellness.get("hrv") or 0.0)
        hrv_sd = 0.0
        hrv_lower_threshold = hrv_baseline * 0.85

    today_hrv = float(latest_wellness.get("hrv") or 0.0)
    hrv_drop = ((hrv_baseline - today_hrv) / hrv_baseline) if (today_hrv > 0 and hrv_baseline > 0) else 0.0

    overrides = []

    # 1. Spadek HRV
    if today_hrv > 0 and ((today_hrv < hrv_lower_threshold and hrv_drop >= 0.08) or hrv_drop > 0.15):
        drop_pct = int(hrv_drop * 100) if hrv_drop > 0 else 0
        overrides.append(f"HRV_OUT_OF_BASELINE_{drop_pct}%")

    # 2. Skok RHR (Tętno spoczynkowe)
    prior_rhrs = [
        float(w.get("restingHR") if w.get("restingHR") is not None else w.get("resting_hr", 0))
        for w in sorted_wellness
        if str(w.get("date") or w.get("id") or "") < target_date
        and (w.get("restingHR") is not None or w.get("resting_hr") is not None)
    ]
    today_rhr_raw = latest_wellness.get("restingHR") if latest_wellness.get("restingHR") is not None else latest_wellness.get("resting_hr")
    if prior_rhrs and today_rhr_raw is not None:
        rhr_baseline = sum(prior_rhrs) / len(prior_rhrs)
        today_rhr = float(today_rhr_raw)
        rhr_diff = today_rhr - rhr_baseline
        if rhr_diff >= 5.0:
            overrides.append(f"RHR_SPIKE_+{int(rhr_diff)}BPM")

    # 3. Dryf tętna (Decoupling) & Compliance
    if compliance:
        decoupling = compliance.get("decoupling")
        if decoupling is not None and decoupling > 10.0:
            overrides.append(f"HIGH_DECOUPLING_{decoupling:.1f}%")
        elif compliance.get("has_aerobic_drift"):
            overrides.append("AEROBIC_DRIFT")

        status_type = compliance.get("status_type")
        if status_type == "SKIP":
            overrides.append("WORKOUT_SKIPPED")
        elif status_type == "EXTRA" and (compliance.get("actual_tss") or 0) >= 60:
            overrides.append(f"UNPLANNED_SESSION_TSS_{int(compliance['actual_tss'])}")

    # 4. TSB Extreme Fatigue
    tsb = latest_wellness.get("tsb")
    if tsb is not None and float(tsb) < -25.0:
        overrides.append(f"EXTREME_FATIGUE_TSB_{int(tsb)}")

    # 5. Słaba jakość snu (< 50/100 lub feeling/sleepQuality == 4)
    sleep_score = latest_wellness.get("sleepScore") if latest_wellness.get("sleepScore") is not None else latest_wellness.get("sleep_score")
    if sleep_score is not None and float(sleep_score) < 50:
        overrides.append(f"POOR_SLEEP_{int(sleep_score)}")
    elif latest_wellness.get("feeling") == 4 or latest_wellness.get("sleepQuality") == 4:
        overrides.append("POOR_SUBJECTIVE_WELLNESS")

    forced_decision = None
    if any(o.startswith(("HRV_", "RHR_SPIKE", "EXTREME_FATIGUE", "POOR_SLEEP")) for o in overrides):
        forced_decision = "CANCEL"  # Twardy nakaz odpoczynku (REST)
    elif overrides:
        forced_decision = "MODIFY"  # Modyfikacja planu

    return latest_wellness, hrv_drop, overrides, forced_decision


class WellnessEvaluator:
    @staticmethod
    async def evaluate_daily_readiness(
        wellness_data: list[Dict[str, Any]], 
        activities_data: list[Dict[str, Any]], 
        planned_today: list[Dict[str, Any]],
        today_str: Optional[str] = None,
        compliance: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str, Optional[str], List[str]]:
        """
        Ocenia przy użyciu deterministycznych Guardrails (Python) oraz opcjonalnie Gemini AI
        czy dzisiejszy plan wymaga interwencji (Needs Recovery).
        Zwraca: (wymaga_interwencji, powod, forced_decision, overrides_list)
        """
        if not wellness_data:
            return False, "Brak danych wellness.", None, []

        latest_w, hrv_drop, overrides, forced_decision = check_tactical_overrides(
            wellness_data, today_str=today_str, compliance=compliance
        )

        if forced_decision == "CANCEL":
            reason = f"DETERMINISTYCZNY OVERRIDE ZDROWOTNY: {', '.join(overrides)}. Twardy nakaz odpoczynku (CANCEL)."
            return True, reason, "CANCEL", overrides

        # Wklejanie do f-stringów
        wellness_str = json.dumps([{
            "date": w.get("date") or w.get("id"),
            "hrv": w.get("hrv"),
            "rhr": w.get("restingHR") or w.get("resting_hr"),
            "sleep_quality": w.get("sleepQuality") or w.get("sleepScore"),
            "feeling": w.get("feeling")
        } for w in wellness_data[-30:] if w])

        activities_str = json.dumps([{
             "date": str(a.get("start_date_local", "")).split("T")[0],
             "type": a.get("type"),
             "tss": a.get("icu_training_load") or a.get("training_load") or a.get("tss")
        } for a in activities_data[-30:] if a])
        
        planned_str = json.dumps([{
             "date": str(p.get("date", "")),
             "type": p.get("workout_type") or p.get("type"),
             "name": p.get("name"),
             "tss": p.get("planned_tss") or p.get("icu_training_load")
        } for p in planned_today])

        prompt = build_ai_wellness_evaluation_prompt(wellness_str, activities_str, planned_str)
        
        try:
            client = GeminiClient()
            result = await client.generate_structured(prompt, WellnessEvaluationResult)
            
            if result:
                ret_decision = result.forced_decision or forced_decision
                return result.needs_revision, result.reason, ret_decision, overrides
            return False, "Błąd modelu (Pusty obiekt).", forced_decision, overrides
        except Exception as e:
            print(f"Błąd ewaluacji AI Wellness: {e}")
            if forced_decision:
                return True, f"Fallback: Wykryto overrides ({', '.join(overrides)})", forced_decision, overrides
            return False, "Fallback: Parametry w normie.", None, overrides


