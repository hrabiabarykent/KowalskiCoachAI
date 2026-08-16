from sqlalchemy import Column, Integer, String, Float, JSON, Date, ForeignKey
from sqlalchemy.orm import relationship
from datetime import date
from app.database import Base

class AthleteSnapshot(Base):
    __tablename__ = "athlete_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(Date, default=date.today)
    resting_hr = Column(Integer, nullable=True)
    hrv = Column(Float, nullable=True) # Zmienna do gotowości bazy nocnej
    sleep_score = Column(Float, nullable=True) # Ocena snu z intervals (jesli dostepna)
    subjective_feeling = Column(Integer, nullable=True) # 1-5 subiektywna ocena

    all_activities_year = Column(JSON, nullable=True)
    activities_42d = Column(JSON, nullable=True)

    # PMC
    ctl = Column(Integer)
    atl = Column(Integer)
    tsb = Column(Integer)

    # Curves
    power_curve_42d = Column(JSON)
    power_curve_year = Column(JSON)
    pace_curve_42d = Column(JSON)
    pace_curve_year = Column(JSON)

    # Stats
    stats_42d = Column(JSON)
    stats_year = Column(JSON)

    # Key metrics
    estimated_ftp = Column(Float)
    estimated_vdot = Column(Float)

    # Profile
    gender = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    weight = Column(Float, nullable=True)

    # AI assessment
    ai_assessment = Column(String, nullable=True)

    user = relationship("User", back_populates="snapshots")
