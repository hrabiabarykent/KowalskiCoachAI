import pytest
from app.domain.metrics import (
    format_seconds_to_pace,
    mps_to_pace,
    vdot_from_5k_minutes,
    vdot_from_wkg,
    parse_pace_str,
    parse_time_to_minutes,
    calculate_hrv_status,
    calculate_training_readiness,
    extract_record_val
)

def test_format_seconds_to_pace():
    assert format_seconds_to_pace(255) == "4:15"
    assert format_seconds_to_pace(300) == "5:00"
    assert format_seconds_to_pace(0) == "N/A"
    assert format_seconds_to_pace(-10) == "N/A"

def test_mps_to_pace():
    # 4.0 m/s = 250s/km = 4:10
    assert mps_to_pace(4.0) == "4:10"
    assert mps_to_pace(0) == "N/A"

def test_vdot_from_5k_minutes():
    # 5k w 20 minut -> VDOT ok 50.0
    vdot = vdot_from_5k_minutes(20.0)
    assert 48.0 <= vdot <= 52.0
    # Wartości skrajne
    assert vdot_from_5k_minutes(0) == 0.0
    assert vdot_from_5k_minutes(250) == 0.0

def test_vdot_from_wkg():
    # 4.0 W/kg -> 10.8 * 4.0 + 7 = 50.2
    assert vdot_from_wkg(4.0) == 50.2
    assert vdot_from_wkg(0) == 0.0

def test_parse_pace_str():
    assert parse_pace_str("04:15") == 255
    assert parse_pace_str("5:00") == 300
    assert parse_pace_str("invalid") is None

def test_parse_time_to_minutes():
    assert parse_time_to_minutes("01:30") == 90
    assert parse_time_to_minutes("") == 0

def test_calculate_hrv_status():
    # Optymalne HRV (ratio 1.0)
    status, details = calculate_hrv_status(60.0, 60.0)
    assert status == "Zrównoważony"
    assert details["ratio"] == 1.0

    # Spadek HRV (ratio 0.90)
    status, details = calculate_hrv_status(54.0, 60.0)
    assert status == "Niezrównoważony"

    # Drastyczny spadek HRV (ratio 0.80)
    status, details = calculate_hrv_status(48.0, 60.0)
    assert status == "Niski"

    # Brak bazy
    status, _ = calculate_hrv_status(60.0, 0.0)
    assert status == "Brak Bazy"

def test_calculate_training_readiness():
    # Idealne warunki (dobry sen, wysokie TSB, optymalne HRV)
    score, details = calculate_training_readiness(
        hrv_status_ratio=1.0,
        sleep_score=95.0,
        tsb=10.0,
        atl=50.0,
        rhr_ratio=1.0
    )
    assert score >= 90

    # Trudny dzień (niski HRV, niski TSB, wyższe RHR)
    score_low, details_low = calculate_training_readiness(
        hrv_status_ratio=0.80,
        sleep_score=40.0,
        tsb=-20.0,
        atl=90.0,
        rhr_ratio=1.08
    )
    assert score_low < 50
    assert details_low["hrv_penalty"] < 0
    assert details_low["rhr_penalty"] < 0

def test_extract_record_val_power():
    curve = {
        "list": [
            {
                "secs": [5, 60, 300, 1200, 3600],
                "watts": [600, 400, 320, 280, 250]
            }
        ]
    }
    # Rekord mocy na 5 minut (300 sek)
    res = extract_record_val(curve, 300, is_pace=False)
    assert res == "320W"

def test_extract_record_val_pace():
    curve = {
        "list": [
            {
                "distance": [1000, 5000, 10000],
                "values": [240, 1250, 2600] # całkowity czas w sekundach
            }
        ]
    }
    # Rekord tempa na 5km (5000m): 1250s / 5km = 250 s/km = 4:10
    res = extract_record_val(curve, 5000, is_pace=True)
    assert res == "4:10"
