import pytest
from app.domain.workout_compiler import (
    Step,
    RepeatBlock,
    StructuredWorkout,
    build_intervals_dsl,
    build_event_payload
)

def test_step_validation():
    step = Step(duration_min=5.0, target="Z2", label="Rozgrzewka")
    assert step.duration_min == 5.0
    assert step.target == "Z2"
    assert step.label == "Rozgrzewka"

    with pytest.raises(ValueError):
        Step(duration_min=0, target="Z2")

    with pytest.raises(ValueError):
        Step(duration_min=5, target="   ")

def test_build_intervals_dsl_simple():
    workout = StructuredWorkout(
        name="Prostki Bieg Z2",
        blocks=[
            RepeatBlock(
                reps=1,
                steps=[
                    Step(duration_min=10.0, target="Z1", label="Rozgrzewka"),
                    Step(duration_min=30.0, target="Z2", label="Bieg główny"),
                    Step(duration_min=5.0, target="Z1", label="Schłodzenie")
                ]
            )
        ]
    )

    dsl = build_intervals_dsl(workout)
    expected = (
        "- 10m Z1 Rozgrzewka\n"
        "- 30m Z2 Bieg główny\n"
        "- 5m Z1 Schłodzenie"
    )
    assert dsl == expected

def test_build_intervals_dsl_repeats():
    workout = StructuredWorkout(
        name="Interwały 5x3m Z4",
        blocks=[
            RepeatBlock(
                reps=1,
                steps=[Step(duration_min=15.0, target="Z2", label="Rozgrzewka")]
            ),
            RepeatBlock(
                reps=5,
                steps=[
                    Step(duration_min=3.0, target="105% Z4", label="Interwał"),
                    Step(duration_min=2.0, target="55% Z1", label="Regeneracja")
                ]
            ),
            RepeatBlock(
                reps=1,
                steps=[Step(duration_min=10.0, target="Z1", label="Schłodzenie")]
            )
        ]
    )

    dsl = build_intervals_dsl(workout)
    assert "5x" in dsl
    assert "- 3m 105% Z4 Interwał" in dsl
    assert "- 2m 55% Z1 Regeneracja" in dsl

def test_build_event_payload():
    payload = build_event_payload(
        date_iso="2026-08-06",
        workout_name="Interwały Z4",
        workout_type="Run",
        planned_tss=65.0,
        moving_min=45.0,
        dsl_text="- 45m Z2"
    )

    assert payload["category"] == "WORKOUT"
    assert payload["start_date_local"] == "2026-08-06T07:00:00"
    assert payload["name"] == "[Kowalski] Interwały Z4"
    assert payload["type"] == "Run"
    assert payload["icu_training_load"] == 65
    assert payload["moving_time"] == 2700
    assert payload["description"] == "[Kowalski]\n- 45m Z2"

def test_20_diverse_workouts_dsl():
    from tests.fixtures.workouts_fixture import generate_20_test_workouts
    workouts = generate_20_test_workouts()
    assert len(workouts) == 20

    for w in workouts:
        dsl = build_intervals_dsl(w)
        assert len(dsl.strip()) > 0
        assert "\n\n\n" not in dsl

        total_min = sum(sum(s.duration_min for s in b.steps) * b.reps for b in w.blocks)
        payload = build_event_payload(
            date_iso="2026-08-06",
            workout_name=w.name,
            workout_type="Run",
            planned_tss=50.0,
            moving_min=total_min,
            dsl_text=dsl
        )

        assert payload["name"].startswith("[Kowalski]")
        assert payload["description"].startswith("[Kowalski]")
        assert payload["moving_time"] == int(round(total_min * 60))

