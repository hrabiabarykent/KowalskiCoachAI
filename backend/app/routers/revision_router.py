from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.daily_revision_service import DailyRevisionService

router = APIRouter(prefix="/revision", tags=["Revision"])

@router.post("/approve/{plan_id}")
async def approve_revision(plan_id: int, db: Session = Depends(get_db)):
    """Aprobuje proponowane przez AI zmiany (zastępuje PENDING nowymi PROPOSED)."""
    service = DailyRevisionService(db)
    success, message = await service.approve_revision_for_plan(plan_id)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"status": "success", "message": message}

@router.post("/reject/{plan_id}")
async def reject_revision(plan_id: int, db: Session = Depends(get_db)):
    """Odrzuca proponowane przez AI zmiany (usuwa PROPOSED, zachowuje stary plan)."""
    service = DailyRevisionService(db)
    success, message = await service.reject_revision_for_plan(plan_id)
    if not success:
        raise HTTPException(status_code=400, detail=message)
@router.get("/debug/{user_id}")
async def debug_revision(user_id: int, db: Session = Depends(get_db)):
    """Pobiera i wyświetla surowy prompt oraz odpowiedź z modelu AI dla zadanego użytkownika bez modyfikacji bazy danych."""
    service = DailyRevisionService(db)
    result = await service.debug_daily_revision_for_user(user_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result
