from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date, timedelta
from typing import List, Optional

from app.database import get_db
from app.models.training_plan import TrainingPlan, PlanStatus
from app.models.planned_workout import PlannedWorkout, WorkoutStatus
from app.models.microcycle import Microcycle
from app.models.user import User
from app.models.annual_plan import AnnualTrainingPlan
from app.schemas.microcycle import (
    MicrocycleGenerateRequest,
    MicrocycleSummaryResponse,
    MicrocycleDetailResponse,
    PlannedWorkoutCreate,
    PlannedWorkoutUpdate,
    PlannedWorkoutResponse
)
from app.services.microcycle_service import MicrocycleService
from app.domain.workout_compiler import build_intervals_dsl, StructuredWorkout
from app.integrations.intervals_client import IntervalsClient

router = APIRouter(prefix="/plan", tags=["Plan"])

@router.get("/{user_id}")
async def get_user_plan(user_id: int, db: Session = Depends(get_db)):
    """Pobiera obecny plan użytkownika, aktywny mikrocykl i nadchodzące treningi."""
    atp_record = db.query(AnnualTrainingPlan).filter(AnnualTrainingPlan.user_id == user_id).order_by(AnnualTrainingPlan.created_at.desc()).first()
    atp_data = atp_record.plan_data if atp_record else None
    
    # 1. Szukamy aktywnego planu lub planu oczekującego na akceptację
    plan = db.query(TrainingPlan).filter(
        TrainingPlan.user_id == user_id,
        TrainingPlan.status.in_([PlanStatus.ACTIVE, PlanStatus.PENDING_APPROVAL])
    ).first()
    
    if not plan:
        return {"has_plan": False, "plan": None, "workouts": [], "microcycles": [], "annual_training_plan": atp_data}
        
    # 2. Pobieramy treningi od dzisiaj na najbliższe 7 dni
    today = date.today()
    end_date = today + timedelta(days=7)
    
    workouts = db.query(PlannedWorkout).filter(
        PlannedWorkout.plan_id == plan.id,
        PlannedWorkout.date >= today,
        PlannedWorkout.date <= end_date,
        PlannedWorkout.status.in_([WorkoutStatus.PENDING, WorkoutStatus.PROPOSED])
    ).order_by(PlannedWorkout.date).all()
    
    # Pobieramy ostatnie mikrocykle
    microcycles = db.query(Microcycle).filter(Microcycle.plan_id == plan.id).order_by(Microcycle.start_date.desc()).limit(10).all()
    microcycles_summary = [
        MicrocycleService.get_microcycle_detail(db, mc.id) for mc in microcycles
    ]

    # 3. Dodajemy zewnętrzne nadchodzące treningi z Intervals.icu
    intervals_events = []
    user = db.query(User).filter(User.id == user_id).first()
    if user and user.intervals_id and user.intervals_api_key:
        try:
            client = IntervalsClient(api_key=user.intervals_api_key)
            client.base_url = f"https://intervals.icu/api/v1/athlete/{user.intervals_id}"
            raw_events = await client.get_events(today.isoformat(), end_date.isoformat())
            
            for ev in raw_events:
                intervals_events.append({
                    "id": f"intervals_{ev.get('id')}",
                    "date": ev.get("start_date_local", "")[:10],
                    "name": ev.get("name", "Trening"),
                    "workout_type": ev.get("type", "Inne"),
                    "intensity_category": "AEROBIC_BASE",
                    "is_key_workout": False,
                    "planned_duration_minutes": round(ev.get("moving_time", 0) / 60) if ev.get("moving_time") else 0,
                    "planned_tss": ev.get("icu_training_load", 0),
                    "description": ev.get("description", ""),
                    "workout_doc": ev.get("workout_doc", None),
                    "status": "APPROVED",
                    "source": "intervals",
                    "color": ev.get("color", "#4DA8DA")
                })
        except Exception as e:
            print(f"Błąd pobierania kalendarza Intervals: {e}")

    # 4. Łączymy i formatujemy
    local_workouts_formatted = [
        {
            "id": str(w.id),
            "microcycle_id": w.microcycle_id,
            "date": str(w.date),
            "name": w.name,
            "workout_type": w.workout_type,
            "intensity_category": w.intensity_category,
            "is_key_workout": w.is_key_workout or False,
            "description": w.description or "",
            "workout_doc": w.structure or None,
            "planned_duration_minutes": w.planned_duration_minutes,
            "planned_tss": w.planned_tss,
            "status": w.status,
            "source": "local"
        } for w in workouts
    ]
    
    all_workouts = local_workouts_formatted + intervals_events
    all_workouts.sort(key=lambda x: x["date"])
    
    return {
        "has_plan": True,
        "plan": {
            "id": plan.id,
            "status": plan.status,
            "current_phase": plan.current_phase
        },
        "workouts": all_workouts,
        "microcycles": microcycles_summary,
        "annual_training_plan": atp_data
    }

# ----------------- Mikrocykle Endpoints -----------------

@router.post("/microcycle/generate")
async def generate_microcycle(req: MicrocycleGenerateRequest, db: Session = Depends(get_db)):
    """Generuje nowy mikrocykl dla użytkownika na podstawie ATP i założonych celów."""
    mc = await MicrocycleService.generate_microcycle(
        db=db,
        user_id=req.user_id,
        plan_id=req.plan_id,
        week_number=req.week_number,
        start_date=req.start_date,
        target_tss=req.target_tss,
        goal_id=req.goal_id,
        focus=req.focus
    )
    detail = MicrocycleService.get_microcycle_detail(db, mc.id)
    return {"success": True, "microcycle": detail}

@router.get("/microcycle/{microcycle_id}")
async def get_microcycle(microcycle_id: int, db: Session = Depends(get_db)):
    """Pobiera szczegóły danego mikrocyklu wraz z przypisanymi treningami."""
    detail = MicrocycleService.get_microcycle_detail(db, microcycle_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Mikrocykl nie istnieje")
    return detail

@router.post("/microcycle/{microcycle_id}/sync-intervals")
async def sync_microcycle_to_intervals(microcycle_id: int, db: Session = Depends(get_db)):
    """Wysyła zaplanowane treningi mikrocyklu do kalendarza Intervals.icu."""
    mc = db.query(Microcycle).filter(Microcycle.id == microcycle_id).first()
    if not mc:
        raise HTTPException(status_code=404, detail="Mikrocykl nie istnieje")
    
    plan = db.query(TrainingPlan).filter(TrainingPlan.id == mc.plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Powiązany plan treningowy nie istnieje")
    
    user = db.query(User).filter(User.id == plan.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Użytkownik nie istnieje")

    result = await MicrocycleService.sync_to_intervals(db, user, microcycle_id)
    return result

# ----------------- Jednostki Treningowe (CRUD) -----------------

@router.post("/workout")
async def create_workout(req: PlannedWorkoutCreate, db: Session = Depends(get_db)):
    """Tworzy nową jednostkę treningową (ręcznie lub z automatyczną kompilacją DSL)."""
    # Jeśli podano microcycle_id, upewnijmy się, że plan_id jest zgodny
    plan_id = req.plan_id
    if req.microcycle_id and not plan_id:
        mc = db.query(Microcycle).filter(Microcycle.id == req.microcycle_id).first()
        if mc:
            plan_id = mc.plan_id

    if not plan_id:
        # Pobierz pierwszy aktywny plan
        first_plan = db.query(TrainingPlan).first()
        plan_id = first_plan.id if first_plan else None

    # Opcjonalne wygenerowanie tekstu DSL jeśli przekazano strukturę JSON
    dsl_desc = req.description or ""
    if req.structure and not dsl_desc:
        try:
            structured_obj = StructuredWorkout.model_validate(req.structure)
            dsl_desc = build_intervals_dsl(structured_obj)
        except Exception:
            dsl_desc = req.description or ""

    workout = PlannedWorkout(
        plan_id=plan_id,
        microcycle_id=req.microcycle_id,
        date=req.date,
        workout_type=req.workout_type,
        intensity_category=req.intensity_category,
        is_key_workout=req.is_key_workout,
        name=req.name,
        description=dsl_desc,
        structure=req.structure,
        planned_tss=req.planned_tss,
        planned_duration_minutes=req.planned_duration_minutes,
        status=req.status
    )
    db.add(workout)
    db.commit()
    db.refresh(workout)

    return {"success": True, "workout_id": workout.id, "workout": workout}

@router.put("/workout/{workout_id}")
async def update_workout(workout_id: int, req: PlannedWorkoutUpdate, db: Session = Depends(get_db)):
    """Aktualizuje istniejącą jednostkę treningową."""
    workout = db.query(PlannedWorkout).filter(PlannedWorkout.id == workout_id).first()
    if not workout:
        raise HTTPException(status_code=404, detail="Trening nie istnieje")

    update_data = req.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(workout, key, value)

    # Re-kompilacja DSL jeśli zaktualizowano structure
    if "structure" in update_data and workout.structure:
        try:
            structured_obj = StructuredWorkout.model_validate(workout.structure)
            workout.description = build_intervals_dsl(structured_obj)
        except Exception:
            pass

    db.commit()
    db.refresh(workout)
    return {"success": True, "workout": workout}

@router.delete("/workout/{workout_id}")
async def delete_workout(workout_id: int, db: Session = Depends(get_db)):
    """Usuwa jednostkę treningową."""
    workout = db.query(PlannedWorkout).filter(PlannedWorkout.id == workout_id).first()
    if not workout:
        raise HTTPException(status_code=404, detail="Trening nie istnieje")

    db.delete(workout)
    db.commit()
    return {"success": True, "deleted_id": workout_id}
