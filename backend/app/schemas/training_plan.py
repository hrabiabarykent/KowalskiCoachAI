from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import date, datetime

class PlanPhase(str):
    pass # Pydantic v2 radzi sobie lepiej z enumami bezpośrednio, ale dla prostoty DTO można zostawić str

class PlannedWorkoutBase(BaseModel):
    date: date
    workout_type: str
    name: str
    description: Optional[str] = None
    structure: Optional[Dict[str, Any]] = None
    planned_tss: Optional[float] = None
    planned_duration_minutes: Optional[int] = None

class PlannedWorkoutCreate(PlannedWorkoutBase):
    plan_id: int

class PlannedWorkoutResponse(PlannedWorkoutBase):
    id: int
    plan_id: int
    status: str
    intervals_event_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TrainingPlanBase(BaseModel):
    name: str = "Training Plan"
    start_date: date
    end_date: Optional[date] = None
    current_phase: str = "Base"

class TrainingPlanCreate(TrainingPlanBase):
    user_id: int
    goal_ids: Optional[List[int]] = None

class TrainingPlanResponse(TrainingPlanBase):
    id: int
    user_id: int
    status: str
    created_at: datetime
    updated_at: datetime
    planned_workouts: List[PlannedWorkoutResponse] = []

    class Config:
        from_attributes = True
