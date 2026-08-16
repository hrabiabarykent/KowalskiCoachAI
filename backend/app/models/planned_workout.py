from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey, DateTime, JSON, Float
from sqlalchemy.orm import relationship
import enum
from app.database import Base

class WorkoutStatus(str, enum.Enum):
    PENDING = "Pending"
    COMPLETED = "Completed"
    MISSED = "Missed"
    SKIPPED = "Skipped" # Celowo pominięty na rzecz recovery
    PROPOSED = "Proposed" # Niewymuszony jeszcze plan AI oczekujący na akceptację user'a

class PlannedWorkout(Base):
    __tablename__ = "planned_workouts"
    
    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("training_plans.id"))
    microcycle_id = Column(Integer, ForeignKey("microcycles.id"), nullable=True)
    
    date = Column(Date, index=True)
    workout_type = Column(String) # np. V02Max, Endurance, Recovery, Tempo, SweetSpot
    intensity_category = Column(String, nullable=True) # np. RECOVERY, AEROBIC_BASE, THRESHOLD, VO2MAX
    is_key_workout = Column(Boolean, default=False)
    
    name = Column(String)
    description = Column(String, nullable=True)
    structure = Column(JSON, nullable=True) # Struktura np. kroków do wysłania na Garmin
    
    planned_tss = Column(Float, nullable=True)
    planned_duration_minutes = Column(Integer, nullable=True)
    
    status = Column(String, default=WorkoutStatus.PENDING)
    
    # ID zewnetrznego systemu (Intervals.icu) aby mozna było modyfikować istniejący wpis
    intervals_event_id = Column(String, nullable=True, index=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relacje
    plan = relationship("TrainingPlan", back_populates="planned_workouts")
    microcycle = relationship("Microcycle", back_populates="planned_workouts")
