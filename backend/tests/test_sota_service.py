import pytest
from unittest.mock import MagicMock
from app.services.sota_service import SotaService, SotaPassportMetric
from app.models.snapshot import AthleteSnapshot

def test_sota_passport_metric_dict():
    metric = SotaPassportMetric(250.0, "MEASURED", "Moc maksymalna z mocomierza")
    d = metric.to_dict()
    assert d["value"] == 250.0
    assert d["source_type"] == "MEASURED"
    assert "mocomierza" in d["annotation"]

def test_extract_power_duration_curve_metrics():
    curve_data = {
        "list": [
            {
                "secs": [5, 60, 300, 1200, 3600],
                "watts": [650, 420, 330, 280, 250]
            }
        ]
    }

    metrics = SotaService.extract_power_duration_curve_metrics(curve_data)
    assert metrics["5s"]["value"] == "650W"
    assert metrics["5s"]["source_type"] == "MEASURED"

    assert metrics["5m"]["value"] == "330W"
    assert metrics["5m"]["source_type"] == "MEASURED"

def test_determine_ftp_and_vdot_sources():
    # Przypadek 1: FTP estymowane z modelu, VDOT zmierzone z biegu 5k
    intervals_data = {
        "athlete": {"weight": 70.0},
        "pc_bike_year": {
            "list": [
                {"powerModels": [{"ftp": 260.0, "type": "Morton 3P"}]}
            ]
        },
        "pc_run_year": {
            "list": [
                {
                    "distance": [5000],
                    "values": [1200] # 20 minut -> VDOT ~ 50
                }
            ]
        }
    }

    ftp_m, vdot_m = SotaService.determine_ftp_and_vdot(intervals_data)
    assert ftp_m.value == 260.0
    assert ftp_m.source_type == "ESTIMATED"
    assert "Morton 3P" in ftp_m.annotation

    assert vdot_m.value > 45.0
    assert vdot_m.source_type == "MEASURED"
    assert "zegarka GPS" in vdot_m.annotation

def test_determine_ftp_user_declared():
    # Przypadek 2: FTP wpisane ręcznie w profilu
    intervals_data = {
        "athlete": {"ftp": 230.0, "weight": 75.0},
        "pc_bike_year": {},
        "pc_run_year": {}
    }

    ftp_m, vdot_m = SotaService.determine_ftp_and_vdot(intervals_data)
    assert ftp_m.value == 230.0
    assert ftp_m.source_type == "USER_DECLARED"
    assert "profilu" in ftp_m.annotation
