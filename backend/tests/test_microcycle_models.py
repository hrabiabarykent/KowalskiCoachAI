import pytest
from datetime import date, timedelta
from pydantic import ValidationError

from app.models.user import User
from app.models.training_plan import TrainingPlan, PlanPhase, PlanStatus
from app.models.goal import TrainingGoal
from app.models.microcycle import Microcycle, MicrocycleStatus
from app.models.planned_workout import PlannedWorkout, WorkoutStatus
from app.schemas.microcycle import (
    MicrocycleCreate,
    MicrocycleDetailResponse,
    PlannedWorkoutCreate,
    PlannedWorkoutResponse
)

def test_create_microcycle_record(db_session):
    """Sprawdza tworzenie rekordu Microcycle w bazie danych."""
    user = User(email="test@kowalskicoach.ai", intervals_id="i123", intervals_api_key="key123")
    db_session.add(user)
    db_session.commit()

    plan = TrainingPlan(user_id=user.id, name="Sezon 2026", start_date=date.today(), current_phase=PlanPhase.BASE)
    db_session.add(plan)
    db_session.commit()

    start_d = date.today()
    end_d = start_d + timedelta(days=6)

    microcycle = Microcycle(
        plan_id=plan.id,
        week_number=1,
        start_date=start_d,
        end_date=end_d,
        phase="Base",
        focus="Adaptacja i tlenowa baza Z2",
        target_tss=420.0,
        target_hours=8.5,
        status=MicrocycleStatus.DRAFT
    )
    db_session.add(microcycle)
    db_session.commit()

    saved = db_session.query(Microcycle).filter(Microcycle.id == microcycle.id).first()
    assert saved is not None
    assert saved.week_number == 1
    assert saved.target_tss == 420.0
    assert saved.status == MicrocycleStatus.DRAFT
    assert saved.plan.name == "Sezon 2026"

def test_microcycle_relationships_and_cascade(db_session):
    """Weryfikuje relacje i kaskadowe usuwanie jednostek treningowych po usunięciu mikrocyklu."""
    user = User(email="cascade@kowalskicoach.ai")
    db_session.add(user)
    db_session.commit()

    plan = TrainingPlan(user_id=user.id, start_date=date.today())
    db_session.add(plan)
    db_session.commit()

    goal = TrainingGoal(user_id=user.id, priority="A", discipline="Bike", event_name="Tatra Road Race", event_date=date.today() + timedelta(days=60))
    db_session.add(goal)
    db_session.commit()

    microcycle = Microcycle(
        plan_id=plan.id,
        goal_id=goal.id,
        week_number=5,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=6),
        phase="Build",
        target_tss=500.0
    )
    db_session.add(microcycle)
    db_session.commit()

    workout1 = PlannedWorkout(
        plan_id=plan.id,
        microcycle_id=microcycle.id,
        date=date.today(),
        workout_type="Bike",
        intensity_category="THRESHOLD",
        is_key_workout=True,
        name="Sweet Spot 3x10min",
        planned_tss=75.0,
        planned_duration_minutes=75
    )
    workout2 = PlannedWorkout(
        plan_id=plan.id,
        microcycle_id=microcycle.id,
        date=date.today() + timedelta(days=1),
        workout_type="Bike",
        intensity_category="RECOVERY",
        is_key_workout=False,
        name="Regeneracja Z1",
        planned_tss=20.0,
        planned_duration_minutes=40
    )
    db_session.add_all([workout1, workout2])
    db_session.commit()

    # Sprawdzenie powiązań
    assert len(microcycle.planned_workouts) == 2
    assert microcycle.goal.event_name == "Tatra Road Race"

    # Usunięcie mikrocyklu i sprawdzenie kaskadowości
    db_session.delete(microcycle)
    db_session.commit()

    remaining_workouts = db_session.query(PlannedWorkout).filter(PlannedWorkout.microcycle_id == microcycle.id).all()
    assert len(remaining_workouts) == 0

def test_microcycle_pydantic_schemas():
    """Weryfikuje poprawność schematów Pydantic v2 dla mikrocykli."""
    valid_data = {
        "plan_id": 1,
        "week_number": 3,
        "start_date": "2026-08-18",
        "end_date": "2026-08-24",
        "phase": "Build",
        "focus": "Próg tlenowy i siła na podjazdach",
        "target_tss": 480.0,
        "target_hours": 9.0,
        "status": "Active"
    }
    schema = MicrocycleCreate.model_validate(valid_data)
    assert schema.week_number == 3
    assert schema.target_tss == 480.0

    # Test błędu braku wymaganych pól
    with pytest.raises(ValidationError):
        MicrocycleCreate.model_validate({"phase": "Build"})
