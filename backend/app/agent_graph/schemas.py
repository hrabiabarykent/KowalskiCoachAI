from pydantic import BaseModel, Field
from typing import List, Optional

class PhysiologyVerdict(BaseModel):
    status: str = Field(..., description="Stan zawodnika: GREEN, YELLOW, lub RED")
    max_tss: float = Field(..., description="Maksymalny dopuszczalny TSS na dzisiaj")
    allowed_zones: List[str] = Field(..., description="Dopuszczalne strefy treningowe np. ['Z1', 'Z2']")
    recovery_required: bool = Field(..., description="Czy wymagany jest odpoczynek")
    notes: str = Field(..., description="Uzasadnienie fizjologiczne")

class WorkoutProposal(BaseModel):
    workout_name: str = Field(..., description="Nazwa treningu")
    workout_type: str = Field(..., description="Dyscyplina: Run, Bike, Swim")
    planned_duration_min: float = Field(..., description="Planowany czas w minutach")
    planned_tss: float = Field(..., description="Wyliczony TSS")
    dsl_text: str = Field(..., description="Kod treningowy w formacie Intervals DSL (np. '- 30m Z1')")
    reasoning: str = Field(..., description="Uzasadnienie trenerskie doboru sesji")

class CritiqueResult(BaseModel):
    decision: str = Field(..., description="Decyzja sędziowska: APPROVED lub REJECTED")
    violations: List[str] = Field(default_factory=list, description="Lista wykrytych naruszeń reguł fizjologicznych")
    required_fixes: List[str] = Field(default_factory=list, description="Instrukcje poprawek dla WorkoutPlannerAgent")
