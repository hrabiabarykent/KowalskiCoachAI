from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.goal import TrainingGoal
from app.models.snapshot import AthleteSnapshot
from app.schemas.user import UserSetup
from datetime import date

router = APIRouter()

@router.get("/debug/{user_id}")
def get_debug_data(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    goals = db.query(TrainingGoal).filter(TrainingGoal.user_id == user_id).all()
    
    # Get the latest snapshot
    snapshot = db.query(AthleteSnapshot).filter(AthleteSnapshot.user_id == user_id).order_by(AthleteSnapshot.date.desc()).first()
    
    return {
        "user": {
            "id": user.id,
            "username": user.username,
            "intervals_id": user.intervals_id,
            "has_intervals_api_key": bool(user.intervals_api_key),
            "training_availability": user.training_availability
        },
        "goals": [
            {
                "id": g.id,
                "priority": g.priority,
                "discipline": g.discipline,
                "event_type": g.event_type,
                "event_name": g.event_name,
                "event_date": g.event_date.isoformat() if g.event_date else None,
                "target_time_minutes": g.target_time_minutes,
                "is_recreational": g.is_recreational,
                "created_at": g.created_at.isoformat() if g.created_at else None,
                "ai_evaluation": g.ai_evaluation
            } for g in goals
        ],
        "latest_snapshot": {
            "id": snapshot.id,
            "date": snapshot.date.isoformat() if snapshot.date else None,
            "resting_hr": snapshot.resting_hr,
            "ctl": snapshot.ctl,
            "atl": snapshot.atl,
            "tsb": snapshot.tsb,
            "estimated_ftp": snapshot.estimated_ftp,
            "estimated_vdot": snapshot.estimated_vdot,
            "gender": snapshot.gender,
            "age": snapshot.age,
            "weight": snapshot.weight,
            "stats_year": snapshot.stats_year,
            "power_curve_year": snapshot.power_curve_year,
            "pace_curve_year": snapshot.pace_curve_year,
            "ai_assessment": snapshot.ai_assessment
        } if snapshot else None
    }
