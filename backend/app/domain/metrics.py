from typing import Optional
import math

def format_seconds_to_pace(seconds: float) -> str:
    if not seconds or seconds <= 0: return "N/A"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}:{secs:02d}"

def mps_to_pace(mps: float) -> str:
    if not mps or mps <= 0: return "N/A"
    return format_seconds_to_pace(1000 / mps)

def extract_record_val(curve_response, target, is_pace=False):
    """
    Ekstrahuje rekordy z krzywej mocy (target w sek) lub tempa (target w metrach).
    Obsługuje formaty z Intervals.icu z elastycznym dopasowaniem najbliższego / najlepszego punktu.
    """
    if not curve_response:
        return "N/A"
        
    container = []
    if isinstance(curve_response, list): 
        container = curve_response
    elif isinstance(curve_response, dict):
        container = curve_response.get("list") or curve_response.get("curve") or [curve_response]
        
    if not container:
        return "N/A"
        
    try:
        curve = container[0] if isinstance(container, list) and len(container) > 0 else curve_response
        
        if is_pace:
            x_arr = curve.get("distance") or curve.get("distances") or curve.get("dist") or []
            y_arr = curve.get("values") or curve.get("secs") or []
        else:
            x_arr = curve.get("secs") or curve.get("seconds") or []
            y_arr = curve.get("watts") or curve.get("values") or []
            
        if not x_arr or not y_arr or len(x_arr) != len(y_arr):
            return "N/A"
            
        x_y_map = dict(zip(x_arr, y_arr))

        # 1. Dokładny mecz
        if target in x_y_map and x_y_map[target] is not None and float(x_y_map[target]) > 0:
            val = float(x_y_map[target])
            if is_pace:
                pace_sec_per_km = (val / float(target)) * 1000.0
                return format_seconds_to_pace(pace_sec_per_km)
            return f"{int(val)}W"

        # 2. Szukanie najlepszego dopasowania
        if is_pace:
            valid_indices = [i for i, x in enumerate(x_arr) if abs(x - target) <= target * 0.15]
            if not valid_indices:
                valid_indices = [min(range(len(x_arr)), key=lambda i: abs(x_arr[i] - target))]

            best_idx = min(valid_indices, key=lambda i: abs(x_arr[i] - target))
            actual_x = float(x_arr[best_idx])
            total_sec = float(y_arr[best_idx])
            if actual_x > 0 and total_sec > 0:
                pace_sec_per_km = (total_sec / actual_x) * 1000.0
                return format_seconds_to_pace(pace_sec_per_km)
        else:
            valid_secs = [s for s in x_arr if s <= target]
            best_s = max(valid_secs) if valid_secs else min(x_arr, key=lambda s: abs(s - target))
            w = x_y_map.get(best_s)
            if w and float(w) > 0:
                return f"{int(w)}W"

        return "N/A"
    except Exception as e:
        print(f"Error in extract_record_val: {e}")
        return "N/A"


def vdot_from_wkg(wkg: float) -> float:
    return round(10.8 * wkg + 7, 1) if wkg > 0 else 0.0

def vdot_from_5k_minutes(t: float) -> float:
    if t <= 0 or t > 200: return 0.0
    v = 5000 / t
    # Koszt tlenowy przy prędkości v
    vo2_cost = -4.6 + 0.182258 * v + 0.000104 * (v**2)
    # Intensywność (% VDOT) możliwa do utrzymania przez czas t
    percent_vdot = 0.8 + 0.189437 * math.exp(-0.012778 * t) + 0.2989558 * math.exp(-0.19326 * t)
    vdot = vo2_cost / percent_vdot
    return round(vdot, 1)

def parse_pace_str(pace: str) -> Optional[float]:
    try:
        m, s = pace.split(":")
        return int(m) * 60 + int(s)
    except: return None

def parse_time_to_minutes(time_str: str) -> int:
    if not time_str: return 0
    try:
        parts = list(map(int, time_str.split(':')))
        return parts[0] * 60 + parts[1]
    except: return 0

def calculate_hrv_status(hrv_7d_avg: float, hrv_30d_baseline: float) -> tuple[str, dict]:
    """Zwraca status HRV podobny do Garmin na podstawie porównania średniej 7-dniowej do bazy 30-dniowej. Zwraca: (Status, Szczegóły)"""
    details = {
        "hrv_7d_avg": round(hrv_7d_avg, 1),
        "hrv_30d_baseline": round(hrv_30d_baseline, 1),
        "ratio": 0.0,
        "calculation": "7d avg / 30d baseline"
    }

    if hrv_30d_baseline == 0:
        details["reason"] = "Brak zarejestrowanej bazy 30 dniowej."
        return "Brak Bazy", details
    
    ratio = hrv_7d_avg / hrv_30d_baseline
    details["ratio"] = round(ratio, 2)
    
    if 0.97 <= ratio <= 1.05:
        details["reason"] = "W stosunku do Twojej bazy, obecne HRV jest optymalne."
        return "Zrównoważony", details
    elif 0.85 <= ratio < 0.97:
        details["reason"] = "Twój średni wynik zmienności tętna z 7 dni spadł poniżej punktu odniesienia. Duże obciążenie mogło spowodować ten spadek."
        return "Niezrównoważony", details
    elif ratio < 0.85:
        details["reason"] = "Twoje HRV drastycznie spadło. Znaczne przemęczenie organizmu."
        return "Niski", details
    else:
        details["reason"] = "Twoje HRV jest zauważalnie wyższe od normy, co może być oznaką przemęczenia współczulnego."
        return "Zbyt wysoki", details

def calculate_training_readiness(
    hrv_status_ratio: float, 
    sleep_score: float, 
    tsb: float, 
    atl: float,
    rhr_ratio: float = 1.0
) -> tuple[int, dict]:
    """Oblicza gotowość treningową (0-100) i zwraca słownik debugujący, by zrozumieć wynik."""
    from typing import Any
    
    # Zabezpieczenia przed wartościami None
    if sleep_score is None:
        sleep_score = 0.0
    if tsb is None:
        tsb = 0.0
    if atl is None:
        atl = 0.0
    if rhr_ratio is None:
        rhr_ratio = 1.0
    if hrv_status_ratio is None:
        hrv_status_ratio = 1.0
        
    score = 100.0
    inputs_dict: dict[str, Any] = {
        "hrv_ratio": round(hrv_status_ratio, 2),
        "sleep_score_input": sleep_score,
        "tsb_input": round(tsb, 1),
        "atl": round(atl, 1),
        "rhr_ratio": round(rhr_ratio, 2)
    }
    
    details: dict[str, Any] = {
        "starting_score": 100,
        "hrv_penalty": 0.0,
        "sleep_penalty": 0.0,
        "tsb_penalty": 0.0,
        "rhr_penalty": 0.0,
        "inputs": inputs_dict
    }
    
    # 1. HRV Penalty
    if hrv_status_ratio < 0.97:
        # Niezrównoważony kosztuje bazowo 30 punktów plus skalowanie
        penalty = 30.0 + (0.97 - hrv_status_ratio) * 500.0
        score -= penalty
        details["hrv_penalty"] = round(-penalty, 1)
        
    elif hrv_status_ratio > 1.06:
        # Zbyt wysoki kosztuje 20 pkt plus skalowanie
        penalty = 20.0 + (hrv_status_ratio - 1.06) * 500.0
        score -= penalty
        details["hrv_penalty"] = round(-penalty, 1)
        
    # 2. Sen (Intervals daje sleepScore 0-100 LUB sleepQuality 1-4. Normalize do 100)
    sleep_perc = (sleep_score / 4.0) * 100 if sleep_score <= 4 and sleep_score > 0 else sleep_score
    if sleep_perc == 0:
        sleep_perc = 75.0 # Baza

    details["inputs"]["sleep_normalized_perc"] = round(sleep_perc, 1)
    
    if sleep_perc < 90:
        penalty = (90 - sleep_perc) * 0.8
        score -= penalty
        details["sleep_penalty"] = round(-penalty, 1)
        
    # 3. Odpoczynek/TSB
    # TSB optymalnie ok 10.
    if tsb < 10:
        penalty = (10 - tsb) * 0.7
        score -= penalty
        details["tsb_penalty"] = round(-penalty, 1)
    
    # Przemęczenie kumuluje większe kary
    if tsb < -15:
        extra_penalty = abs(tsb + 15) * 1.5
        score -= extra_penalty
        details["tsb_penalty"] = round(details.get("tsb_penalty", 0) - extra_penalty, 1)
        
    # 4. RHR Penalty (Tętno spoczynkowe)
    # Wyższe RHR = większe przemęczenie. rhr_ratio > 1.0 oznacza wzrost rhr ponad bazę.
    if rhr_ratio > 1.03:
        # np. jeśli rhr wzrosło o 5% (1.05), to ucinamy punkty:
        penalty = (rhr_ratio - 1.03) * 300.0  # 1.05 -> 0.02 * 300 = 6 pkt
        score -= penalty
        details["rhr_penalty"] = round(-penalty, 1)
        
    # Zabezpieczenia na granice 0 - 100
    v = int(score) if isinstance(score, (int, float)) else 100
    final_score = max(0, min(100, v))
    details["final_score"] = final_score
    
    return final_score, details


def classify_day(
    day_events: list[dict],
    day_activities: list[dict]
) -> str:
    """
    Zwraca kategorię dnia na podstawie listy eventów i aktywności z danego dnia:
    - 'REST'     : brak zaplanowanych treningów i brak aktywności
    - 'SKIP'     : był zaplanowany co najmniej jeden trening, brak jakiejkolwiek aktywności
    - 'EXTRA'    : brak zaplanowanych treningów, ale wykonano co najmniej jedną aktywność
    - 'EXECUTED' : były zaplanowane treningi i wykonano co najmniej jedną aktywność
    """
    workout_events = [
        e for e in (day_events or [])
        if e.get("category") == "WORKOUT" or (e.get("icu_training_load") or e.get("planned_tss") or 0) > 0
    ]

    has_event = len(workout_events) > 0
    has_activity = len(day_activities or []) > 0

    if not has_event and not has_activity:
        return "REST"
    if has_event and not has_activity:
        return "SKIP"
    if not has_event and has_activity:
        return "EXTRA"
    return "EXECUTED"


def calculate_compliance(
    day_events: list[dict],
    day_activities: list[dict]
) -> dict:
    """
    Oblicza matematyczną zgodność z planem (Compliance) dla danego dnia,
    uwzględniając tolerancję TSS oraz kary za dryf kardio (Aerobic Decoupling) w Z2.
    """
    workout_events = [
        e for e in (day_events or [])
        if e.get("category") == "WORKOUT" or (e.get("icu_training_load") or e.get("planned_tss") or 0) > 0
    ]
    day_type = classify_day(day_events, day_activities)

    planned_tss = sum(
        float(e.get("icu_training_load") or e.get("planned_load") or e.get("planned_tss") or 0)
        for e in workout_events
    )
    actual_tss = sum(
        float(a.get("icu_training_load") or a.get("training_load") or a.get("tss") or 0)
        for a in (day_activities or [])
    )

    main_activity = max(
        day_activities,
        key=lambda a: float(a.get("icu_training_load") or a.get("training_load") or a.get("tss") or 0)
    ) if day_activities else None
    main_event = workout_events[0] if workout_events else None

    # Reguła: Decoupling liczony TYLKO dla długich treningów tlenowych (TSS > 100 i IF < 80%)
    if main_activity:
        act_tss = float(main_activity.get("icu_training_load") or main_activity.get("training_load") or main_activity.get("tss") or 0)
        raw_if = float(main_activity.get("icu_intensity") or main_activity.get("intensity") or 0)
        act_if = raw_if * 100.0 if (0 < raw_if <= 1.0) else raw_if
        is_long_aerobic = (act_tss > 100.0 and 0.0 < act_if < 80.0)
    else:
        is_long_aerobic = False

    raw_decoupling = main_activity.get("decoupling") if main_activity else None
    decoupling = float(raw_decoupling) if (raw_decoupling is not None and is_long_aerobic) else None

    if day_type == "REST":
        return {
            "status_type": "REST",
            "score": None,
            "label": "Rest / Brak planu",
            "planned_tss": 0.0,
            "actual_tss": 0.0,
            "delta_tss": 0.0,
            "within_tolerance": True,
            "decoupling": None,
            "is_long_aerobic": False,
            "has_aerobic_drift": False,
            "notes": "Dzień bez zaplanowanego treningu i bez zarejestrowanej aktywności.",
            "main_activity": None,
            "main_event": None
        }

    if day_type == "SKIP":
        event_names = ", ".join(e.get("name", "Trening") for e in workout_events)
        return {
            "status_type": "SKIP",
            "score": 0,
            "label": "Skip (Zaplanowany, niewykonany)",
            "planned_tss": planned_tss,
            "actual_tss": 0.0,
            "delta_tss": -planned_tss,
            "within_tolerance": False,
            "decoupling": None,
            "is_long_aerobic": False,
            "has_aerobic_drift": False,
            "notes": f"Trening '{event_names}' (TSS {planned_tss:.0f}) został pominięty.",
            "main_activity": None,
            "main_event": main_event
        }

    if day_type == "EXTRA":
        act_names = ", ".join(a.get("name", "Aktywność") for a in (day_activities or []))
        return {
            "status_type": "EXTRA",
            "score": None,
            "label": "Extra (Nieplanowany)",
            "planned_tss": 0.0,
            "actual_tss": actual_tss,
            "delta_tss": actual_tss,
            "within_tolerance": False,
            "decoupling": decoupling,
            "is_long_aerobic": is_long_aerobic,
            "has_aerobic_drift": (decoupling is not None and decoupling > 7.0),
            "notes": f"Wykonano dodatkową aktywność '{act_names}' (TSS {actual_tss:.0f}).",
            "main_activity": main_activity,
            "main_event": None
        }

    # EXECUTED (Trening zaplanowany i wykonany)
    delta_tss = actual_tss - planned_tss
    abs_delta = abs(delta_tss)

    if planned_tss < 45:
        tolerance_desc = "±15 TSS (Mała jednostka)"
        within_tolerance = abs_delta <= 15.0
        excess = max(0.0, abs_delta - 15.0)
        tss_penalty = min(5.0, round(excess / 10.0, 1))
    else:
        allowed_delta = planned_tss * 0.15
        tolerance_desc = f"±15% (±{allowed_delta:.1f} TSS)"
        within_tolerance = abs_delta <= allowed_delta
        excess = max(0.0, abs_delta - allowed_delta)
        tss_penalty = min(5.0, round((excess / planned_tss) * 10.0, 1)) if planned_tss > 0 else 0.0

    has_aerobic_drift = (decoupling is not None and decoupling > 7.0)
    if decoupling is None or decoupling <= 5.0:
        decoupling_penalty = 0.0
    elif decoupling <= 7.0:
        decoupling_penalty = 1.0
    elif decoupling <= 10.0:
        decoupling_penalty = 2.0
    else:
        decoupling_penalty = 3.5

    raw_score = 10.0 - tss_penalty - decoupling_penalty
    score = max(1, min(10, int(round(raw_score))))

    act_name = main_activity.get("name") if main_activity else "Trening"
    return {
        "status_type": "EXECUTED",
        "score": score,
        "label": f"Executed ({score}/10)",
        "planned_tss": planned_tss,
        "actual_tss": actual_tss,
        "delta_tss": delta_tss,
        "tolerance_desc": tolerance_desc,
        "within_tolerance": within_tolerance,
        "tss_penalty": tss_penalty,
        "decoupling": decoupling,
        "is_long_aerobic": is_long_aerobic,
        "has_aerobic_drift": has_aerobic_drift,
        "decoupling_penalty": decoupling_penalty,
        "notes": f"Trening '{act_name}' zrealizowany.",
        "main_activity": main_activity,
        "main_event": main_event
    }

