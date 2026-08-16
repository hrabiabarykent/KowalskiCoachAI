import pytest
from app.domain.wellness_evaluator import check_tactical_overrides, WellnessEvaluator
from app.domain.metrics import classify_day, calculate_compliance

def test_check_tactical_overrides_hrv_drop():
    # 30 dni stabilnego HRV ~ 60, dzisiaj spadek na 45 (>15% spadek)
    wellness_list = []
    for i in range(30, 0, -1):
        wellness_list.append({"date": f"2026-07-{i:02d}", "hrv": 60, "restingHR": 48})
    wellness_list.append({"date": "2026-08-01", "hrv": 45, "restingHR": 48})

    latest, hrv_drop, overrides, forced_decision = check_tactical_overrides(wellness_list, today_str="2026-08-01")
    assert forced_decision == "CANCEL"
    assert any("HRV_OUT_OF_BASELINE" in o for o in overrides)
    assert hrv_drop > 0.15

def test_check_tactical_overrides_rhr_spike():
    # RHR bazowo 48, dzisiaj 54 (+6 bpm skok)
    wellness_list = []
    for i in range(30, 0, -1):
        wellness_list.append({"date": f"2026-07-{i:02d}", "hrv": 60, "restingHR": 48})
    wellness_list.append({"date": "2026-08-01", "hrv": 60, "restingHR": 54})

    latest, hrv_drop, overrides, forced_decision = check_tactical_overrides(wellness_list, today_str="2026-08-01")
    assert forced_decision == "CANCEL"
    assert any("RHR_SPIKE" in o for o in overrides)

def test_check_tactical_overrides_normal():
    # Normalny dzień - brak overrides
    wellness_list = []
    for i in range(30, 0, -1):
        wellness_list.append({"date": f"2026-07-{i:02d}", "hrv": 60, "restingHR": 48})
    wellness_list.append({"date": "2026-08-01", "hrv": 59, "restingHR": 49})

    latest, hrv_drop, overrides, forced_decision = check_tactical_overrides(wellness_list, today_str="2026-08-01")
    assert forced_decision is None
    assert len(overrides) == 0

def test_classify_day():
    event = [{"category": "WORKOUT", "icu_training_load": 50}]
    activity = [{"type": "Run", "icu_training_load": 52}]

    assert classify_day([], []) == "REST"
    assert classify_day(event, []) == "SKIP"
    assert classify_day([], activity) == "EXTRA"
    assert classify_day(event, activity) == "EXECUTED"

def test_calculate_compliance_executed_ideal():
    events = [{"category": "WORKOUT", "icu_training_load": 100, "name": "Long Ride Z2"}]
    activities = [{
        "type": "Ride",
        "icu_training_load": 102,
        "icu_intensity": 70, # IF 70%
        "decoupling": 3.2,
        "name": "Long Ride Z2"
    }]

    comp = calculate_compliance(events, activities)
    assert comp["status_type"] == "EXECUTED"
    assert comp["score"] == 10
    assert comp["within_tolerance"] is True
    assert comp["has_aerobic_drift"] is False

def test_calculate_compliance_executed_decoupling_penalty():
    events = [{"category": "WORKOUT", "icu_training_load": 120, "name": "Long Run Z2"}]
    activities = [{
        "type": "Run",
        "icu_training_load": 120,
        "icu_intensity": 75, # IF 75%
        "decoupling": 11.4, # Dryf > 10%
        "name": "Long Run Z2"
    }]

    comp = calculate_compliance(events, activities)
    assert comp["status_type"] == "EXECUTED"
    assert comp["score"] <= 7 # Nakładasz 3.5 pkt kary
    assert comp["has_aerobic_drift"] is True
    assert comp["decoupling_penalty"] == 3.5

def test_calculate_compliance_skip():
    events = [{"category": "WORKOUT", "icu_training_load": 80, "name": "Intervals Z4"}]
    comp = calculate_compliance(events, [])
    assert comp["status_type"] == "SKIP"
    assert comp["score"] == 0
    assert comp["planned_tss"] == 80.0
    assert comp["actual_tss"] == 0.0
