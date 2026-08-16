import pytest
from datetime import date, timedelta

from app.models.user import User
from app.models.goal import TrainingGoal
from app.models.training_plan import TrainingPlan, PlanPhase
from app.domain.microcycle_allocator import MicrocycleAllocator
from app.services.microcycle_service import MicrocycleService

def test_microcycle_allocator_availability_respect():
    """Weryfikuje, że dni z zerową dostępnością generują dni odpoczynku (REST, 0 TSS)."""
    start_d = date(2026, 8, 17) # Poniedziałek
    custom_avail = {
        0: 0.0, # Poniedziałek: Wolne
        1: 2.0, # Wtorek
        2: 1.0, # Środa
        3: 0.0, # Czwartek: Wolne
        4: 1.5, # Piątek
        5: 3.0, # Sobota
        6: 0.0  # Niedziela: Wolne
    }

    allocations = MicrocycleAllocator.allocate_week(
        start_date=start_d,
        phase="Build",
        target_tss=450.0,
        primary_discipline="Bike",
        availability_map=custom_avail
    )

    assert len(allocations) == 7
    # Poniedziałek (0), Czwartek (3), Niedziela (6) muszą być REST
    assert allocations[0].intensity_category == "REST"
    assert allocations[0].target_tss == 0.0
    assert allocations[3].intensity_category == "REST"
    assert allocations[6].intensity_category == "REST"

def test_microcycle_allocator_accent_spacing():
    """Sprawdza, że główne akcenty są rozdzielone dniami regeneracji / lżejszej pracy."""
    start_d = date(2026, 8, 17)
    allocations = MicrocycleAllocator.allocate_week(
        start_date=start_d,
        phase="Build",
        target_tss=500.0,
        primary_discipline="Bike"
    )

    key_accents = [d for d in allocations if d.is_key_accent]
    assert len(key_accents) >= 2

    # Sprawdzenie czy żaden akcent nie występuje w kolejnych bezpośrednio po sobie dniach
    for i in range(len(allocations) - 1):
        if allocations[i].is_key_accent and allocations[i].intensity_category in ["THRESHOLD", "VO2MAX"]:
            next_day = allocations[i + 1]
            assert not (next_day.is_key_accent and next_day.intensity_category in ["THRESHOLD", "VO2MAX"]), \
                f"Dzień {allocations[i].date} i {next_day.date} mają bezpośrednio po sobie ciężkie akcenty!"

def test_microcycle_allocator_taper_reduction():
    """Weryfikuje redukcję obciążenia w fazie Taper / Recovery."""
    start_d = date(2026, 8, 17)
    build_alloc = MicrocycleAllocator.allocate_week(start_d, phase="Build", target_tss=500.0)
    taper_alloc = MicrocycleAllocator.allocate_week(start_d, phase="Taper", target_tss=500.0)

    total_build_tss = sum(d.target_tss for d in build_alloc)
    total_taper_tss = sum(d.target_tss for d in taper_alloc)

    assert total_taper_tss < total_build_tss
    assert total_taper_tss <= 350.0 # Redukcja ~40%

@pytest.mark.asyncio
async def test_microcycle_service_generation(db_session):
    """Testuje pełną generację mikrocyklu przez MicrocycleService z bazą danych."""
    user = User(email="cyclist@kowalskicoach.ai")
    db_session.add(user)
    db_session.commit()

    goal = TrainingGoal(
        user_id=user.id,
        priority="A",
        discipline="Bike",
        event_name="Wyścig Mistrzowski 120km",
        event_date=date.today() + timedelta(days=40)
    )
    db_session.add(goal)
    db_session.commit()

    mc = await MicrocycleService.generate_microcycle(
        db=db_session,
        user_id=user.id,
        goal_id=goal.id,
        target_tss=450.0,
        focus="Praca nad progiem FTP i kadencją"
    )

    assert mc is not None
    assert mc.id is not None
    assert mc.goal_id == goal.id
    assert mc.target_tss == 450.0

    # Sprawdzenie szczegółów mikrocyklu
    detail = MicrocycleService.get_microcycle_detail(db_session, mc.id)
    assert detail is not None
    assert detail["goal_name"] == "Wyścig Mistrzowski 120km"
    assert len(detail["workouts"]) == 7
    assert detail["total_planned_tss"] > 0
