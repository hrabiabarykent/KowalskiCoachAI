from pydantic import BaseModel
from typing import Optional

class GoalInput(BaseModel):
    user_id: int
    priority: str
    discipline: str
    event_type: str
    event_name: str
    event_date: str
    target_time_str: Optional[str] = None
    is_recreational: bool = False


class GoalEvaluationScenario(BaseModel):
    name: str
    target_ctl: int
    weekly_hours_required: float
    success_probability_pct: int
    risk_level: str
    description: str


class GoalEvaluationResponse(BaseModel):
    ambitious_scenario: GoalEvaluationScenario
    realistic_scenario: GoalEvaluationScenario
    safe_scenario: GoalEvaluationScenario
    key_limiters: list[str]
    verdict_summary: str

