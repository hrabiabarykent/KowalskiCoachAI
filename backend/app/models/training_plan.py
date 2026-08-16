from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
import enum
from app.database import Base

class PlanPhase(str, enum.Enum):
    BASE = "Base"
    BUILD = "Build"
    PEAK = "Peak"
    TAPER = "Taper"

class PlanStatus(str, enum.Enum):
    DRAFT = "Draft" # Oczekuje na zatwierdzenie przez uzytkownika
    PENDING_APPROVAL = "Pending Approval" # Aktywny plan z zawieszoną ewaluacją (AI proponuje korektę, czeka na usera)
    ACTIVE = "Active"
    PAUSED = "Paused"
    COMPLETED = "Completed"
    NEEDS_REVISION = "NeedsRevision"

class TrainingPlan(Base):
    __tablename__ = "training_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    name = Column(String, default="Training Plan")
    start_date = Column(Date)
    end_date = Column(Date, nullable=True) # Może nie mieć końca zdefiniowanego sztywno
    
    current_phase = Column(String, default=PlanPhase.BASE) # Używamy String z wartościami Enum
    status = Column(String, default=PlanStatus.ACTIVE)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relacje
    user = relationship("User", back_populates="training_plans")
    goals = relationship("TrainingGoal", back_populates="training_plan")
    planned_workouts = relationship("PlannedWorkout", back_populates="plan", cascade="all, delete-orphan")
    microcycles = relationship("Microcycle", back_populates="plan", cascade="all, delete-orphan")
