from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base

class TrainingGoal(Base):
    __tablename__ = "training_goals"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    priority = Column(String)  # "A", "B", "C"
    discipline = Column(String) # "Bike", "Run", "Swim", "Triathlon"
    event_type = Column(String)
    event_name = Column(String)
    event_date = Column(Date)
    
    target_time_minutes = Column(Integer, nullable=True)
    is_recreational = Column(Boolean, default=False)
    
    plan_id = Column(Integer, ForeignKey("training_plans.id"), nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    ai_evaluation = Column(String, nullable=True) 

    user = relationship("User", back_populates="goals")
    training_plan = relationship("TrainingPlan", back_populates="goals")
