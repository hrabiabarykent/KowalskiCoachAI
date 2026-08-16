import pytest
from app.domain.prompt_builders import (
    build_wellness_md_table,
    build_activities_md_table,
    build_sota_markdown_prompt_context,
    build_daily_autonomous_revision_prompt
)

def test_build_wellness_md_table():
    wellness_data = [
        {"date": "2026-08-05", "hrv": 55, "restingHR": 48, "sleepScore": 85, "ctl": 12, "atl": 5, "tsb": 7}
    ]
    table = build_wellness_md_table(wellness_data)
    assert "| Data | HRV | RHR | Sleep | CTL | ATL | TSB |" in table
    assert "| 2026-08-05 | 55 | 48 | 85 | 12 | 5 | 7 |" in table

def test_build_activities_md_table():
    activities_data = [
        {"start_date_local": "2026-08-05T08:00:00", "name": "Bieg Z2", "type": "Run", "distance": 8500, "moving_time": 3000, "icu_training_load": 65, "decoupling": 2.1}
    ]
    table = build_activities_md_table(activities_data)
    assert "| Data | Nazwa | Typ | Dystans (km) | Czas (m) | TSS | Decoupling |" in table
    assert "8.5" in table
    assert "2.1%" in table

def test_build_sota_markdown_prompt_context():
    sota_dict = {
        "metrics_summary": {
            "ftp": {"value": 220.0, "source_type": "USER_DECLARED", "annotation": "Profil"},
            "vdot": {"value": 36.2, "source_type": "MEASURED", "annotation": "5k GPS"},
            "weight": {"value": 74.0, "source_type": "USER_DECLARED", "annotation": "Profil"},
            "ctl": 11, "atl": 4, "tsb": 7
        },
        "power_duration_curve_pdc": {
            "5s": {"value": "957W", "source_type": "MEASURED", "annotation": "Sprint"}
        },
        "pace_curve_run": {
            "5k": {"value": "5:14", "source_type": "MEASURED", "annotation": "5k GPS"}
        },
        "physiological_diagnosis": {
            "strengths": ["Sprint 957W"],
            "limiters": ["Niski CTL"]
        }
    }
    md_ctx = build_sota_markdown_prompt_context(sota_dict)
    assert "PASZPORT FIZJOLOGICZNY ZAWODNIKA (SOTA)" in md_ctx
    assert "FTP Rower**: **220.0W**" in md_ctx
    assert "957W" in md_ctx
    assert "5:14" in md_ctx

def test_build_daily_autonomous_revision_prompt():
    prompt = build_daily_autonomous_revision_prompt(
        wellness_data=[{"date": "2026-08-05", "hrv": 55}],
        yesterday_planned_events=[],
        yesterday_executed_activities=[],
        today_planned_events=[],
        user_context="Zawodnik Dardanel",
        today_str="2026-08-06",
        yesterday_str="2026-08-05",
        compliance_fact={"status_type": "PERFECT_EXECUTION", "score": 10, "planned_tss": 50, "actual_tss": 50, "delta_tss": 0},
        guardrails_overrides=["HRV_DROP_WARNING"],
        forced_decision=None
    )
    assert "PRE-COMPUTED FACTS" in prompt
    assert "PERFECT_EXECUTION" in prompt
    assert "HRV_DROP_WARNING" in prompt
