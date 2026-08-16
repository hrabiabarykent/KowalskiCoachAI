from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date, timedelta
import math
import statistics


from app.database import get_db
from app.models.user import User
from app.models.snapshot import AthleteSnapshot
from app.models.goal import TrainingGoal
from app.models.annual_plan import AnnualTrainingPlan
from app.schemas.analysis import AnalysisRequest
from app.core.cache import get_cached_intervals, set_cached_intervals
from app.integrations.intervals_client import IntervalsClient
from app.integrations.llm_client import GeminiClient
from app.services.analysis_service import AnalysisService
from app.domain.performance import extract_zones
from app.domain.metrics import extract_record_val, calculate_hrv_status, calculate_training_readiness

router = APIRouter()
llm_client = GeminiClient('gemini-3.6-flash')
deep_llm_client = GeminiClient('gemini-3.6-flash')



analysis_service = AnalysisService(llm_client=llm_client, deep_llm_client=deep_llm_client)

@router.post("/analyze")
async def analyze(req: AnalysisRequest, db: Session = Depends(get_db)):
    user = db.get(User, req.user_id)
    if not user:
        raise HTTPException(404, "User not found")
        
    intervals = get_cached_intervals(req.user_id)
    if not intervals:
        intervals_client = IntervalsClient(api_key=user.intervals_api_key)
        intervals = await intervals_client.fetch_full_dataset()
        set_cached_intervals(req.user_id, intervals)
    
    snap = await analysis_service.create_or_update_snapshot(db, req.user_id, intervals)
    if not snap:
        raise HTTPException(500, "Error building snapshot")
    
    last_ai = db.query(AthleteSnapshot).filter(
        AthleteSnapshot.user_id == req.user_id, 
        AthleteSnapshot.ai_assessment.isnot(None)
    ).order_by(AthleteSnapshot.date.desc()).first()
    
    if req.force_refresh or not last_ai or (date.today() - last_ai.date).days >= 365:
        ai_text = await analysis_service.get_ai_athlete_assessment(snap)
        snap.ai_assessment = ai_text
        db.commit()
    elif (date.today() - last_ai.date).days >= 1 or (last_ai.ai_assessment == "Nie udało się pobrać porannej diagnozy."):
        from app.services.daily_revision_service import DailyRevisionService
        daily_service = DailyRevisionService(db)
        revision = await daily_service.debug_daily_revision_for_user(req.user_id)
        if revision and revision.get("llm_response_json"):
            r = revision["llm_response_json"]
            ai_text = (
                f"**Ocena dzisiejszego Wellness:** {r.get('wellness_assessment', '')}\n\n"
                f"**Zgodność wczorajszego dnia:** {r.get('compliance_score', '')}/10\n\n"
                f"**Decyzja trenera:** {r.get('decision', '')}\n\n"
                f"**Analiza:** {r.get('modified_workout_description', '')}"
            )
        else:
            ai_text = "Nie udało się pobrać porannej diagnozy."
        snap.ai_assessment = ai_text
        db.commit()
    else:
        ai_text = last_ai.ai_assessment

    athlete = intervals.get("athlete", {})
    latest_well = intervals.get("wellness")[-1] if intervals.get("wellness") else {}
    
    user_goals = db.query(TrainingGoal).filter_by(user_id=req.user_id).all()
    
    # Analyze wellness history for dashboard (up to 90 days)
    wellness_data = intervals.get("wellness", [])
    
    # Calculate 7-day HRV avg and CV
    hrv_7d = [w.get("hrv") for w in wellness_data[-7:] if w.get("hrv") is not None]
    hrv_avg_7d = sum(hrv_7d) / len(hrv_7d) if hrv_7d else 0
    hrv_std_7d = statistics.stdev(hrv_7d) if len(hrv_7d) > 1 else 0

    hrv_cv_7d = (hrv_std_7d / hrv_avg_7d * 100) if hrv_avg_7d > 0 else 0
    
    # Calculate 30-day baseline for HRV
    hrv_30d = [w.get("hrv") for w in wellness_data[-30:] if w.get("hrv") is not None]
    hrv_baseline_30d = sum(hrv_30d) / len(hrv_30d) if hrv_30d else 0
    
    # Extract fitness trends for charts
    fitness_trends = [
        {
            "date": w.get("id"), # "2023-10-01"
            "ctl": w.get("ctl", 0),
            "atl": w.get("atl", 0),
            "tsb": w.get("tsb", 0),
            "hrv": w.get("hrv"),
            "resting_hr": w.get("restingHR")
        } for w in wellness_data[-90:] # usually up to 90 days
    ]
    
    # Calculate weekly HRV for bar chart
    weekly_hrv = []
    if wellness_data:
        reversed_wellness = list(reversed(wellness_data))
        length = len(reversed_wellness)
        for i in range(0, min(90, length), 7):
            chunk = reversed_wellness[i:i+7]
            vals = [w.get("hrv") for w in chunk if w.get("hrv") is not None]
            if vals:
                weekly_hrv.append({
                    "date": chunk[-1].get("id"),
                    "avg_hrv": sum(vals) / len(vals)
                })
        weekly_hrv.reverse()
        
    hrv_status_ratio = (hrv_avg_7d / hrv_baseline_30d) if hrv_baseline_30d > 0 else 1.0
    hrv_status_str, hrv_details = calculate_hrv_status(hrv_avg_7d, hrv_baseline_30d)
    
    # Calculate RHR ratio
    rhr_7d = [w.get("restingHR") for w in wellness_data[-7:] if w.get("restingHR") is not None]
    rhr_avg_7d = sum(rhr_7d) / len(rhr_7d) if rhr_7d else 0
    
    rhr_30d = [w.get("restingHR") for w in wellness_data[-30:] if w.get("restingHR") is not None]
    rhr_baseline_30d = sum(rhr_30d) / len(rhr_30d) if rhr_30d else 0
    
    rhr_ratio = (rhr_avg_7d / rhr_baseline_30d) if rhr_baseline_30d > 0 else 1.0
    
    sleep_score_val = latest_well.get("sleepScore") or latest_well.get("sleepQuality", 0)
    
    readiness_score, readiness_details = calculate_training_readiness(
        hrv_status_ratio=hrv_status_ratio,
        sleep_score=sleep_score_val,
        tsb=latest_well.get("tsb", 0),
        atl=latest_well.get("atl", 0),
        rhr_ratio=rhr_ratio
    )

    return {
        "data": {
            "meta": {"athlete_name": athlete.get("name", "Zawodnik")},
            "ai_assessment": ai_text,
            "pmc": {
                "ctl": int(latest_well.get("ctl", 0)), 
                "atl": int(latest_well.get("atl", 0)), 
                "tsb": int(latest_well.get("tsb", 0)), 
                "hrv": latest_well.get("hrv"), 
                "resting_hr": latest_well.get("restingHR"), 
                "weight_kg": snap.weight,
                "hrv_avg_7d": round(hrv_avg_7d),
                "hrv_cv_7d": round(hrv_cv_7d, 1),
                "hrv_baseline_30d": round(hrv_baseline_30d),
                "readiness_score": readiness_score,
                "readiness_details": readiness_details,
                "hrv_status": hrv_status_str,
                "hrv_details": hrv_details,
                "estimated_ftp": snap.estimated_ftp,
                "estimated_vdot": snap.estimated_vdot
            },
            "fitness_trends": fitness_trends,
            "weekly_hrv": weekly_hrv,
            "records": {
                "run_5k_pace": extract_record_val(intervals.get("pc_run_42d"), 5000, True), 
                "bike_cp20m": extract_record_val(intervals.get("pc_bike_42d"), 1200) if extract_record_val(intervals.get("pc_bike_42d"), 1200) != "N/A" else f"{int(snap.estimated_ftp)}"
            },
            "zones": extract_zones(athlete),
            "user_goals": [
                {
                    "id": g.id, 
                    "name": g.event_name, 
                    "type": g.event_type, 
                    "date": str(g.event_date), 
                    "priority": g.priority, 
                    "ai_evaluation": g.ai_evaluation
                } for g in user_goals
            ]
        }
    }

@router.post("/atp")
async def generate_atp(req: AnalysisRequest, db: Session = Depends(get_db)):
    user = db.get(User, req.user_id)
    if not user:
        raise HTTPException(404, "User not found")
        
    intervals = get_cached_intervals(req.user_id)
    if not intervals:
        intervals_client = IntervalsClient(api_key=user.intervals_api_key)
        intervals = await intervals_client.fetch_full_dataset()
        set_cached_intervals(req.user_id, intervals)
    
    snap = await analysis_service.create_or_update_snapshot(db, req.user_id, intervals)
    if not snap:
        raise HTTPException(500, "Error building snapshot")
    
    # Filter only FUTURE goals
    today = date.today()
    user_goals = db.query(TrainingGoal).filter(
        TrainingGoal.user_id == req.user_id,
        TrainingGoal.event_date >= today
    ).order_by(TrainingGoal.event_date.asc()).all()
    
    if not user_goals:
        return {
            "status": "error",
            "data": {"type": "error", "data": "Brak przyszłych celów. Dodaj cele aby wygenerować plan."}
        }
    
    # Plan dates
    plan_start = today.isoformat()
    plan_end = max(g.event_date for g in user_goals).isoformat()
    total_weeks = max(1, (date.fromisoformat(plan_end) - today).days // 7)
    
    # Availability
    av_data = user.training_availability or {}
    total_planned = sum(d.get("max_hours", 0) for d in av_data.values() if d.get("enabled"))
    weekly_hours = total_planned if total_planned > 0 else 12.0
    
    # Generate ATP
    atp_result = await analysis_service.generate_atp(
        snap=snap, 
        goals=user_goals, 
        weekly_hours=weekly_hours,
        training_availability=av_data,
        plan_start=plan_start,
        plan_end=plan_end,
        total_weeks=total_weeks
    )
    
    # Add goals timeline for frontend markers
    goals_timeline = [
        {
            "name": g.event_name,
            "date": str(g.event_date),
            "priority": g.priority,
            "week_number": max(1, (g.event_date - today).days // 7)
        } for g in user_goals
    ]
    
    if atp_result.get("type") == "structured":
        atp_result["data"]["goals_timeline"] = goals_timeline
        
    # Find or create AnnualTrainingPlan to save the ATP
    db.query(AnnualTrainingPlan).filter(AnnualTrainingPlan.user_id == req.user_id).delete()
    
    new_atp = AnnualTrainingPlan(user_id=req.user_id, plan_data=atp_result)
    db.add(new_atp)
    db.commit()
    
    return {
        "status": "success",
        "data": atp_result
    }

from app.services.sota_service import SotaService

@router.get("/sota-passport/{user_id}")
async def get_sota_passport(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Nie odnaleziono użytkownika")

    snapshot = db.query(AthleteSnapshot).filter(AthleteSnapshot.user_id == user_id).order_by(AthleteSnapshot.date.desc()).first()

    if not snapshot or not snapshot.stats_year:
        if not user.intervals_api_key:
            raise HTTPException(400, "Brak klucza Intervals API Key")
        client = IntervalsClient(api_key=user.intervals_api_key)
        intervals = await client.fetch_full_dataset()
        sota_service = SotaService(db)
        snapshot = sota_service.build_and_save_snapshot(user_id, intervals)

    return {
        "status": "success",
        "user_id": user_id,
        "passport": snapshot.stats_year
    }

