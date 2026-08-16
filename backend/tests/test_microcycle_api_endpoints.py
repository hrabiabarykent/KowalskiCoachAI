import pytest
from datetime import date, timedelta
from app.models.user import User
from app.models.training_plan import TrainingPlan
from app.models.goal import TrainingGoal
from app.models.microcycle import Microcycle
from app.models.planned_workout import PlannedWorkout

@pytest.mark.asyncio
async def test_api_get_plan_structure(async_client, db_session):
    """Sprawdza działanie endpointu GET /plan/{user_id}."""
    user = User(email="test_user@kowalskicoach.ai")
    db_session.add(user)
    db_session.commit()

    res = await async_client.get(f"/plan/{user.id}")
    assert res.status_code == 200
    data = res.json()
    assert "has_plan" in data
    assert "microcycles" in data

@pytest.mark.asyncio
async def test_api_generate_microcycle_flow(async_client, db_session):
    """Sprawdza generowanie mikrocyklu przez POST /plan/microcycle/generate."""
    user = User(email="gen_user@kowalskicoach.ai")
    db_session.add(user)
    db_session.commit()

    goal = TrainingGoal(
        user_id=user.id,
        priority="A",
        discipline="Bike",
        event_name="Gran Fondo Gdynia",
        event_date=date.today() + timedelta(days=30)
    )
    db_session.add(goal)
    db_session.commit()

    payload = {
        "user_id": user.id,
        "week_number": 1,
        "target_tss": 420.0,
        "goal_id": goal.id,
        "focus": "Budowa bazy tlenowej"
    }

    res = await async_client.post("/plan/microcycle/generate", json=payload)
    assert res.status_code == 200
    res_data = res.json()
    assert res_data["success"] is True
    assert res_data["microcycle"]["target_tss"] == 420.0
    assert len(res_data["microcycle"]["workouts"]) == 7

@pytest.mark.asyncio
async def test_api_get_microcycle_detail(async_client, db_session):
    """Sprawdza pobieranie mikrocyklu po ID oraz obsługę 404."""
    # 404 dla nieistniejącego ID
    res404 = await async_client.get("/plan/microcycle/999999")
    assert res404.status_code == 404

    # Utworzenie i odczyt
    user = User(email="detail_user@kowalskicoach.ai")
    db_session.add(user)
    db_session.commit()

    plan = TrainingPlan(user_id=user.id, start_date=date.today())
    db_session.add(plan)
    db_session.commit()

    mc = Microcycle(
        plan_id=plan.id,
        week_number=2,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=6),
        phase="Build",
        target_tss=460.0
    )
    db_session.add(mc)
    db_session.commit()

    res = await async_client.get(f"/plan/microcycle/{mc.id}")
    assert res.status_code == 200
    assert res.json()["week_number"] == 2
    assert res.json()["phase"] == "Build"

@pytest.mark.asyncio
async def test_api_workout_crud_operations(async_client, db_session):
    """Sprawdza tworzenie, edycję i usuwanie treningu przez API."""
    user = User(email="workout_crud@kowalskicoach.ai")
    db_session.add(user)
    db_session.commit()

    plan = TrainingPlan(user_id=user.id, start_date=date.today())
    db_session.add(plan)
    db_session.commit()

    # 1. Tworzenie treningu z ustrukturyzowanymi krokami
    create_payload = {
        "plan_id": plan.id,
        "date": str(date.today()),
        "workout_type": "Bike",
        "intensity_category": "THRESHOLD",
        "is_key_workout": True,
        "name": "Interwały 3x10min SweetSpot",
        "planned_tss": 80.0,
        "planned_duration_minutes": 75,
        "structure": {
            "name": "SweetSpot",
            "blocks": [
                {
                    "reps": 3,
                    "steps": [
                        {"duration_min": 10, "target": "Z4 90%"},
                        {"duration_min": 5, "target": "Z1 50%"}
                    ]
                }
            ]
        }
    }

    res_post = await async_client.post("/plan/workout", json=create_payload)
    assert res_post.status_code == 200
    created = res_post.json()
    workout_id = created["workout_id"]
    assert "3x" in created["workout"]["description"] # Weryfikacja automatycznej kompilacji do DSL

    # 2. Aktualizacja treningu
    update_payload = {
        "planned_tss": 90.0,
        "name": "Zaktualizowane Interwały 3x10min"
    }
    res_put = await async_client.put(f"/plan/workout/{workout_id}", json=update_payload)
    assert res_put.status_code == 200
    assert res_put.json()["workout"]["planned_tss"] == 90.0
    assert res_put.json()["workout"]["name"] == "Zaktualizowane Interwały 3x10min"

    # 3. Usunięcie treningu
    res_del = await async_client.delete(f"/plan/workout/{workout_id}")
    assert res_del.status_code == 200
    assert res_del.json()["success"] is True

    # Sprawdzenie czy trening został usunięty z bazy
    check_deleted = db_session.query(PlannedWorkout).filter(PlannedWorkout.id == workout_id).first()
    assert check_deleted is None
