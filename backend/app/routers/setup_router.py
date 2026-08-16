from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserSetup, TrainingAvailabilityUpdate
from app.domain.performance import EVENT_TYPES

router = APIRouter()

@router.get("/dictionaries")
def dictionaries():
    return EVENT_TYPES

@router.post("/setup-keys")
def setup_keys(data: UserSetup, db: Session = Depends(get_db)):
    user = db.get(User, data.user_id)
    if not user:
        user = User(id=data.user_id, username=f"user_{data.user_id}")
        db.add(user)
    user.intervals_api_key = data.intervals_api_key
    user.intervals_id = data.intervals_id
    db.commit()
    return {"status": "ok"}

@router.get("/user/{user_id}/availability")
def get_availability(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.training_availability or {}

@router.post("/user/{user_id}/availability")
def update_availability(user_id: int, data: TrainingAvailabilityUpdate, db: Session = Depends(get_db)):
    if user_id != data.user_id:
        raise HTTPException(status_code=400, detail="User ID mismatch")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Przekonwertuj słownik modeli Pydantic na zwykły słownik dla kolumny JSON
    user.training_availability = {day: d.model_dump() for day, d in data.availability.items()}
    db.commit()
    return {"status": "ok"}
