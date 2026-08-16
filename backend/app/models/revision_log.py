from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from app.database import Base

class RevisionLog(Base):
    __tablename__ = "revision_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    compliance_score = Column(Integer, nullable=False)
    wellness_assessment = Column(Text, nullable=True)
    decision = Column(String(20), nullable=False) # ACCEPT, MODIFY, CANCEL
    modified_workout_description = Column(Text, nullable=True)
    forced_decision = Column(String(20), nullable=True)
    guardrails_overrides = Column(JSON, nullable=True)
