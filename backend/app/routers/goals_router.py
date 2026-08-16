from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models.goal import TrainingGoal
from app.models.snapshot import AthleteSnapshot
from app.schemas.goal import GoalInput
from app.domain.metrics import parse_time_to_minutes
from app.domain.goal_evaluation import evaluate_goal
from app.integrations.llm_client import GeminiClient
from app.core.config import settings

router = APIRouter()
# Używamy gemini-3.6-flash do analizy celów startowych
llm_client = GeminiClient('gemini-3.6-flash')




@router.post("/goals")
def add_goal(data: GoalInput, db: Session = Depends(get_db)):
    e_date = datetime.strptime(data.event_date, "%Y-%m-%d").date()
    goal = TrainingGoal(
        user_id=data.user_id,
        priority=data.priority,
        discipline=data.discipline,
        event_type=data.event_type,
        event_name=data.event_name,
        event_date=e_date,
        target_time_minutes=parse_time_to_minutes(data.target_time_str),
        is_recreational=data.is_recreational
    )
    db.add(goal)
    db.commit()
    return {"status": "added"}

@router.delete("/goals/{goal_id}")
def delete_goal(goal_id: int, db: Session = Depends(get_db)):
    goal = db.get(TrainingGoal, goal_id)
    if not goal:
        raise HTTPException(404, "Cel nie istnieje")
    db.delete(goal)
    db.commit()
    return {"status": "deleted"}

from app.schemas.goal import GoalInput, GoalEvaluationResponse

@router.post("/evaluate-goal/{goal_id}", response_model=GoalEvaluationResponse)
async def evaluate_goal_endpoint(goal_id: int, db: Session = Depends(get_db)):
    goal = db.get(TrainingGoal, goal_id)
    if not goal:
        raise HTTPException(404, "Cel nie istnieje")
        
    snap = db.query(AthleteSnapshot).filter_by(user_id=goal.user_id).order_by(AthleteSnapshot.date.desc()).first()
    if not snap:
        raise HTTPException(400, "Brak snapshota. Wykonaj synchronizację.")
    
    context = evaluate_goal(goal, snap)
    evaluation_res: GoalEvaluationResponse = await llm_client.generate_structured(context.prompt, GoalEvaluationResponse)
    
    if evaluation_res:
        import json
        goal.ai_evaluation = json.dumps(evaluation_res.model_dump(), ensure_ascii=False)
        db.commit()
    
    return evaluation_res

