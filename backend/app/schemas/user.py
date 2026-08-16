from pydantic import BaseModel
from typing import List, Dict, Optional

class UserSetup(BaseModel):
    user_id: int
    intervals_id: str
    intervals_api_key: str

class DayAvailability(BaseModel):
    enabled: bool
    max_hours: float
    sports: List[str]

class TrainingAvailabilityUpdate(BaseModel):
    user_id: int
    availability: Dict[str, DayAvailability]
