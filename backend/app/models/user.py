from sqlalchemy import Column, Integer, String, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=True)
    email = Column(String, unique=True, index=True, nullable=True)
    intervals_id = Column(String, nullable=True)
    intervals_api_key = Column(String, nullable=True)
    training_availability = Column(JSON, nullable=True)
    
    # Relations
    goals = relationship("TrainingGoal", back_populates="user")
    snapshots = relationship("AthleteSnapshot", back_populates="user")
    training_plans = relationship("TrainingPlan", back_populates="user")
    annual_training_plans = relationship("AnnualTrainingPlan", back_populates="user", cascade="all, delete-orphan")

