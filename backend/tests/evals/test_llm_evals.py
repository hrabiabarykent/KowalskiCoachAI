import pytest
from app.domain.wellness_evaluator import check_tactical_overrides
from app.domain.metrics import calculate_compliance
from app.domain.workout_compiler import build_intervals_dsl, Step, RepeatBlock, StructuredWorkout
from app.core.telemetry import LLMTraceEvent, log_llm_trace

def test_eval_guardrails_safety_override():
    """Ewaluacja bezpieczeństwa: spadek HRV musi BEZWZGLĘDNIE skutkować nakazem CANCEL."""
    wellness_data = [
        {"date": "2026-08-01", "hrv": 60, "restingHR": 48},
        {"date": "2026-08-02", "hrv": 62, "restingHR": 48},
        {"date": "2026-08-03", "hrv": 61, "restingHR": 48},
        {"date": "2026-08-04", "hrv": 60, "restingHR": 48},
        {"date": "2026-08-05", "hrv": 42, "restingHR": 55} # Spadek HRV > 25% + skok RHR
    ]

    latest_w, hrv_drop, overrides, forced_decision = check_tactical_overrides(
        wellness_data, today_str="2026-08-05"
    )

    assert hrv_drop > 0.15
    assert any("HRV_OUT_OF_BASELINE" in o for o in overrides)
    assert forced_decision == "CANCEL"

def test_eval_dsl_compiler_correctness():
    """Ewaluacja kompilatora DSL: struktura treningu musi poprawnie zamieniać się w Intervals DSL."""
    workout = StructuredWorkout(
        name="Akcent Z4 Progowo",
        blocks=[
            RepeatBlock(reps=1, steps=[
                Step(duration_min=15, target="50-60%", label="Warmup")
            ]),
            RepeatBlock(reps=3, steps=[
                Step(duration_min=10, target="Z4", label="Próg"),
                Step(duration_min=5, target="50%", label="Regeneracja")
            ]),
            RepeatBlock(reps=1, steps=[
                Step(duration_min=10, target="50%", label="Cooldown")
            ])
        ]
    )

    dsl = build_intervals_dsl(workout)
    assert "- 15m 50-60% Warmup" in dsl
    assert "3x" in dsl
    assert "- 10m Z4 Próg" in dsl
    assert "- 5m 50% Regeneracja" in dsl

def test_eval_telemetry_trace():
    """Ewaluacja telemetrii: rejestrowanie zdarzeń śledzenia LLM."""
    event = LLMTraceEvent("eval_test", "gemini-3.6-flash", 120.5, 300, 1500, True)
    d = event.to_dict()
    assert d["task_name"] == "eval_test"
    assert d["latency_ms"] == 120.5
    assert d["success"] is True
    log_llm_trace(event)
