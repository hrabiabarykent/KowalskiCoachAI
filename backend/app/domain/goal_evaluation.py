from datetime import date
from typing import Dict, Any, List

from app.domain.metrics import extract_record_val
from app.domain.prompt_builders import build_goal_evaluation_prompt

class GoalEvaluationContext:
    def __init__(self, prompt: str):
        self.prompt = prompt

def evaluate_goal(goal, snap, today: date = date.today()) -> GoalEvaluationContext:
    days_left = (goal.event_date - today).days
    weeks_left = round(days_left / 7, 1)

    recent_list = snap.activities_42d or []
    recent_list.sort(key=lambda x: x['date'], reverse=True)
    
    formatted_activities = "\n".join([
        f"- {a['date']}: {a['name']} ({a['type']}), {a['duration_min']} min, TSS: {a['tss']}"
        for a in recent_list
    ])
    
    stats_y = snap.stats_year or {}
    total_h = sum([v.get("h", 0) for v in stats_y.values() if isinstance(v, dict)])
    avg_weekly_h = round(total_h / 52, 1)

    p1h = extract_record_val(snap.power_curve_year, 3600)
    target_desc = "Ukończenie" if goal.is_recreational else f"Czas: {goal.target_time_minutes} min"

    prompt = build_goal_evaluation_prompt(
        discipline=goal.discipline,
        event_type=goal.event_type,
        event_name=goal.event_name,
        weeks_left=weeks_left,
        target_desc=target_desc,
        formatted_activities=formatted_activities,
        avg_weekly_h=avg_weekly_h,
        ctl=snap.ctl,
        gender=snap.gender,
        age=snap.age,
        weight=snap.weight,
        resting_hr=snap.resting_hr,
        estimated_ftp=snap.estimated_ftp,
        p1h=p1h,
        estimated_vdot=snap.estimated_vdot
    )

    print("\n" + "="*80 + "\n[DEBUG] PROMPT WYSYŁANY DO GEMINI:\n" + prompt + "\n" + "="*80)

    return GoalEvaluationContext(prompt=prompt)
