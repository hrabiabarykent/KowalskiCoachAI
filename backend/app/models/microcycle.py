from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
import enum
from app.database import Base

class MicrocycleStatus(str, enum.Enum):
    DRAFT = "Draft"
    ACTIVE = "Active"
    COMPLETED = "Completed"

class Microcycle(Base):
    __tablename__ = "microcycles"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("training_plans.id"), nullable=False)
    goal_id = Column(Integer, ForeignKey("training_goals.id"), nullable=True)

    week_number = Column(Integer, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    phase = Column(String, default="Base")
    focus = Column(String, nullable=True)
    target_tss = Column(Float, default=0.0)
    target_hours = Column(Float, default=0.0)

    status = Column(String, default=MicrocycleStatus.DRAFT)
    notes = Column(String, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relacje
    plan = relationship("TrainingPlan", back_populates="microcycles")
    goal = relationship("TrainingGoal")
    planned_workouts = relationship("PlannedWorkout", back_populates="microcycle", cascade="all, delete-orphan")
