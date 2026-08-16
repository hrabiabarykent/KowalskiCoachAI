from datetime import date, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.training_plan import TrainingPlan, PlanStatus, PlanPhase
from app.models.microcycle import Microcycle, MicrocycleStatus
from app.models.planned_workout import PlannedWorkout, WorkoutStatus
from app.models.goal import TrainingGoal
from app.models.annual_plan import AnnualTrainingPlan
from app.domain.microcycle_allocator import MicrocycleAllocator
from app.domain.workout_compiler import build_intervals_dsl, build_event_payload, StructuredWorkout, RepeatBlock, Step
from app.integrations.intervals_client import IntervalsClient

class MicrocycleService:
    @classmethod
    async def generate_microcycle(
        cls,
        db: Session,
        user_id: int,
        plan_id: Optional[int] = None,
        week_number: Optional[int] = None,
        start_date: Optional[date] = None,
        target_tss: Optional[float] = None,
        goal_id: Optional[int] = None,
        focus: Optional[str] = None
    ) -> Microcycle:
        # 1. Pobranie lub utworzenie planu
        if plan_id:
            plan = db.query(TrainingPlan).filter(TrainingPlan.id == plan_id).first()
        else:
            plan = db.query(TrainingPlan).filter(
                TrainingPlan.user_id == user_id,
                TrainingPlan.status.in_([PlanStatus.ACTIVE, PlanStatus.PENDING_APPROVAL])
            ).first()

        if not plan:
            plan = TrainingPlan(
                user_id=user_id,
                name="Plan Główny",
                start_date=date.today(),
                current_phase=PlanPhase.BASE,
                status=PlanStatus.ACTIVE
            )
            db.add(plan)
            db.flush()

        # 2. Ustalenie daty startu
        if not start_date:
            # Domyślnie najbliższy poniedziałek
            today = date.today()
            start_date = today + timedelta(days=(7 - today.weekday()) % 7) if today.weekday() != 0 else today
        end_date = start_date + timedelta(days=6)

        # 3. Pobranie ATP dla wyznaczenia fazy i targetu TSS
        atp_rec = db.query(AnnualTrainingPlan).filter(AnnualTrainingPlan.user_id == user_id).order_by(AnnualTrainingPlan.created_at.desc()).first()
        derived_phase = plan.current_phase or "Base"
        derived_tss = target_tss or 400.0
        derived_week_num = week_number or 1

        if atp_rec and atp_rec.plan_data and isinstance(atp_rec.plan_data, dict):
            weeks_data = atp_rec.plan_data.get("data", {}).get("weeks", [])
            if weeks_data:
                # Szukamy tygodnia pasującego datą lub numerem
                matched_w = next((w for w in weeks_data if w.get("week_number") == derived_week_num), weeks_data[0])
                if not target_tss and matched_w.get("target_tss"):
                    derived_tss = float(matched_w.get("target_tss"))
                if matched_w.get("phase"):
                    derived_phase = matched_w.get("phase")

        # 4. Pobranie celu głównego
        target_goal = None
        if goal_id:
            target_goal = db.query(TrainingGoal).filter(TrainingGoal.id == goal_id).first()
        else:
            target_goal = db.query(TrainingGoal).filter(
                TrainingGoal.user_id == user_id,
                TrainingGoal.priority == "A"
            ).first()

        primary_discipline = target_goal.discipline if target_goal and target_goal.discipline else "Bike"
        goal_priority = target_goal.priority if target_goal else "A"

        # 5. Uruchomienie alokatora
        allocations = MicrocycleAllocator.allocate_week(
            start_date=start_date,
            phase=derived_phase,
            target_tss=derived_tss,
            primary_discipline=primary_discipline,
            goal_priority=goal_priority
        )

        # 6. Zapis mikrocyklu do bazy
        microcycle = Microcycle(
            plan_id=plan.id,
            goal_id=target_goal.id if target_goal else None,
            week_number=derived_week_num,
            start_date=start_date,
            end_date=end_date,
            phase=derived_phase,
            focus=focus or f"{derived_phase} - Akcenty {primary_discipline} pod cel {target_goal.event_name if target_goal else 'Ogólny'}",
            target_tss=derived_tss,
            target_hours=round(sum(a.available_hours for a in allocations), 1),
            status=MicrocycleStatus.ACTIVE
        )
        db.add(microcycle)
        db.flush()

        # 7. Utworzenie jednostek treningowych z przykładową kompilacją DSL
        for alloc in allocations:
            if alloc.intensity_category == "REST":
                pw = PlannedWorkout(
                    plan_id=plan.id,
                    microcycle_id=microcycle.id,
                    date=alloc.date,
                    workout_type="Rest",
                    intensity_category="REST",
                    is_key_workout=False,
                    name=alloc.suggested_name,
                    description=alloc.focus_notes,
                    planned_tss=0.0,
                    planned_duration_minutes=0,
                    status=WorkoutStatus.PENDING
                )
            else:
                # Generujemy przykładową strukturę kroków
                if alloc.intensity_category == "THRESHOLD":
                    struct = {
                        "name": alloc.suggested_name,
                        "blocks": [
                            {"reps": 1, "steps": [{"duration_min": 15, "target": "Z2 60%", "label": "Rozgrzewka"}]},
                            {"reps": 3, "steps": [
                                {"duration_min": 10, "target": "Z4 95-105%", "label": "Interwał progowy"},
                                {"duration_min": 5, "target": "Z1 50%", "label": "Odpoczynek"}
                            ]},
                            {"reps": 1, "steps": [{"duration_min": 15, "target": "Z1 55%", "label": "Wyciszenie"}]}
                        ]
                    }
                elif alloc.intensity_category == "VO2MAX":
                    struct = {
                        "name": alloc.suggested_name,
                        "blocks": [
                            {"reps": 1, "steps": [{"duration_min": 15, "target": "Z2 65%", "label": "Rozgrzewka"}]},
                            {"reps": 5, "steps": [
                                {"duration_min": 4, "target": "Z5 110-120%", "label": "VO2Max"},
                                {"duration_min": 4, "target": "Z1 50%", "label": "Regeneracja"}
                            ]},
                            {"reps": 1, "steps": [{"duration_min": 10, "target": "Z1 50%", "label": "Wyciszenie"}]}
                        ]
                    }
                else:
                    # Baza / Regeneracja
                    struct = {
                        "name": alloc.suggested_name,
                        "blocks": [
                            {"reps": 1, "steps": [
                                {"duration_min": alloc.target_duration_minutes, "target": "Z2 65-75%", "label": "Ciągła jazda tlenowa"}
                            ]}
                        ]
                    }

                # Kompilacja DSL
                try:
                    structured_obj = StructuredWorkout.model_validate(struct)
                    dsl_text = build_intervals_dsl(structured_obj)
                except Exception:
                    dsl_text = f"- {alloc.target_duration_minutes}m Z2"

                full_desc = f"{alloc.focus_notes}\n\n{dsl_text}"

                pw = PlannedWorkout(
                    plan_id=plan.id,
                    microcycle_id=microcycle.id,
                    date=alloc.date,
                    workout_type=alloc.workout_type,
                    intensity_category=alloc.intensity_category,
                    is_key_workout=alloc.is_key_accent,
                    name=alloc.suggested_name,
                    description=full_desc,
                    structure=struct,
                    planned_tss=alloc.target_tss,
                    planned_duration_minutes=alloc.target_duration_minutes,
                    status=WorkoutStatus.PENDING
                )
            db.add(pw)

        db.commit()
        db.refresh(microcycle)
        return microcycle

    @classmethod
    def get_microcycle_detail(cls, db: Session, microcycle_id: int) -> Optional[Dict[str, Any]]:
        mc = db.query(Microcycle).filter(Microcycle.id == microcycle_id).first()
        if not mc:
            return None

        workouts = db.query(PlannedWorkout).filter(PlannedWorkout.microcycle_id == mc.id).order_by(PlannedWorkout.date).all()
        total_planned_tss = sum((w.planned_tss or 0.0) for w in workouts)
        total_planned_min = sum((w.planned_duration_minutes or 0) for w in workouts)

        goal = db.query(TrainingGoal).filter(TrainingGoal.id == mc.goal_id).first() if mc.goal_id else None

        return {
            "id": mc.id,
            "plan_id": mc.plan_id,
            "goal_id": mc.goal_id,
            "goal_name": goal.event_name if goal else None,
            "week_number": mc.week_number,
            "start_date": mc.start_date,
            "end_date": mc.end_date,
            "phase": mc.phase,
            "focus": mc.focus,
            "target_tss": mc.target_tss,
            "target_hours": mc.target_hours,
            "total_planned_tss": total_planned_tss,
            "total_planned_minutes": total_planned_min,
            "status": mc.status,
            "notes": mc.notes,
            "workouts": [
                {
                    "id": w.id,
                    "plan_id": w.plan_id,
                    "microcycle_id": w.microcycle_id,
                    "date": w.date,
                    "workout_type": w.workout_type,
                    "intensity_category": w.intensity_category,
                    "is_key_workout": w.is_key_workout,
                    "name": w.name,
                    "description": w.description,
                    "structure": w.structure,
                    "planned_tss": w.planned_tss,
                    "planned_duration_minutes": w.planned_duration_minutes,
                    "status": w.status,
                    "intervals_event_id": w.intervals_event_id,
                    "source": "local"
                } for w in workouts
            ]
        }

    @classmethod
    async def sync_to_intervals(cls, db: Session, user: User, microcycle_id: int) -> Dict[str, Any]:
        if not user.intervals_id or not user.intervals_api_key:
            return {"success": False, "error": "Brak skonfigurowanych kluczy Intervals.icu"}

        mc = db.query(Microcycle).filter(Microcycle.id == microcycle_id).first()
        if not mc:
            return {"success": False, "error": "Mikrocykl nie istnieje"}

        workouts = db.query(PlannedWorkout).filter(
            PlannedWorkout.microcycle_id == mc.id,
            PlannedWorkout.workout_type != "Rest"
        ).all()

        client = IntervalsClient(api_key=user.intervals_api_key)
        client.base_url = f"https://intervals.icu/api/v1/athlete/{user.intervals_id}"

        synced_count = 0
        errors = []

        for w in workouts:
            try:
                # Ekstrakcja DSL lub struktury
                dsl_text = ""
                if w.structure:
                    try:
                        structured = StructuredWorkout.model_validate(w.structure)
                        dsl_text = build_intervals_dsl(structured)
                    except Exception:
                        dsl_text = w.description or ""
                else:
                    dsl_text = w.description or ""

                payload = build_event_payload(
                    date_iso=str(w.date),
                    workout_name=w.name,
                    workout_type=w.workout_type,
                    planned_tss=w.planned_tss or 0.0,
                    moving_min=float(w.planned_duration_minutes or 0),
                    dsl_text=dsl_text
                )

                created_ev = await client.create_event(payload)
                if created_ev and created_ev.get("id"):
                    w.intervals_event_id = str(created_ev.get("id"))
                    synced_count += 1
            except Exception as e:
                errors.append(f"Błąd dla treningu {w.name} ({w.date}): {str(e)}")

        db.commit()
        return {
            "success": True,
            "synced_workouts": synced_count,
            "total_workouts": len(workouts),
            "errors": errors
        }
