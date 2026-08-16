from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import date, datetime

class PlannedWorkoutView(BaseModel):
    name: str = Field(description="Krótka, czytelna nazwa treningu, np. 'Bieg Spokojny 45min + Przebieżki'")
    workout_type: str = Field(description="Główny cel fizjologiczny: 'Recovery', 'Endurance', 'Tempo', 'Threshold', 'VO2Max', 'Anaerobic', 'Strength'")
    day_offset: int = Field(description="Liczba dni od 'jutra', na które zaplanowany jest ten trening. 0 to jutro, 1 to pojutrze, itd.")
    planned_duration_minutes: int = Field(description="Planowany czas trwania w minutach")
    planned_tss: int = Field(description="Szacunkowe obciążenie TSS dla tej jednostki")
    description: Optional[str] = Field(None, description="Szczegółowy opis dla zawodnika, co i jak ma wykonać")

class MicrocyclePlan(BaseModel):
    workouts: List[PlannedWorkoutView] = Field(description="Lista jednostek treningowych na układany mikrocykl")
    coach_comment: str = Field(description="Komentarz trenera Kowalskiego do zawodnika podsumowujący założenia na ten tydzień")

class DailyRevisionResponse(BaseModel):
    needs_revision: bool = Field(description="Czy na podstawie danych (szczególnie sen, HRV) konieczna jest zmiana planu treningowego na dziś lub kolejne dni?")
    reason: str = Field(description="Wytłumaczenie zawodnikowi dlaczego Kowalski decyduje się na zachowanie obecnego planu, lub dlaczego proponuje zmiany ew. odpoczynek.")
    proposed_workouts: List[PlannedWorkoutView] = Field(description="Proponowany nowy plan mikrocyklu od 'jutra', JEŻELI needs_revision to True. Inaczej pusta tablica.")

# Rozszerzone schematy do operacji CRUD i API
class PlannedWorkoutBase(BaseModel):
    date: date
    workout_type: str = Field(..., description="Typ sportu lub jednostki: Bike, Run, Swim, Strength, Rest, itp.")
    intensity_category: Optional[str] = Field("AEROBIC_BASE", description="Kategoria: RECOVERY, AEROBIC_BASE, THRESHOLD, VO2MAX")
    is_key_workout: bool = False
    name: str
    description: Optional[str] = None
    structure: Optional[Dict[str, Any]] = None
    planned_tss: Optional[float] = 0.0
    planned_duration_minutes: Optional[int] = 0
    status: str = "Pending"

class PlannedWorkoutCreate(PlannedWorkoutBase):
    microcycle_id: Optional[int] = None
    plan_id: Optional[int] = None
    generate_ai_structure: bool = False

class PlannedWorkoutUpdate(BaseModel):
    date: Optional[date] = None
    workout_type: Optional[str] = None
    intensity_category: Optional[str] = None
    is_key_workout: Optional[bool] = None
    name: Optional[str] = None
    description: Optional[str] = None
    structure: Optional[Dict[str, Any]] = None
    planned_tss: Optional[float] = None
    planned_duration_minutes: Optional[int] = None
    status: Optional[str] = None

class PlannedWorkoutResponse(PlannedWorkoutBase):
    id: int
    plan_id: Optional[int] = None
    microcycle_id: Optional[int] = None
    intervals_event_id: Optional[str] = None
    source: Optional[str] = "local"
    model_config = ConfigDict(from_attributes=True)

class MicrocycleGenerateRequest(BaseModel):
    user_id: int
    plan_id: Optional[int] = None
    week_number: Optional[int] = None
    start_date: Optional[date] = None
    target_tss: Optional[float] = None
    goal_id: Optional[int] = None
    focus: Optional[str] = None
    preferred_disciplines: Optional[List[str]] = None

class MicrocycleCreate(BaseModel):
    plan_id: int
    goal_id: Optional[int] = None
    week_number: int
    start_date: date
    end_date: date
    phase: str = "Base"
    focus: Optional[str] = None
    target_tss: float = 0.0
    target_hours: float = 0.0
    status: str = "Draft"
    notes: Optional[str] = None

class MicrocycleUpdate(BaseModel):
    goal_id: Optional[int] = None
    focus: Optional[str] = None
    target_tss: Optional[float] = None
    target_hours: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class MicrocycleSummaryResponse(BaseModel):
    id: int
    plan_id: int
    goal_id: Optional[int] = None
    week_number: int
    start_date: date
    end_date: date
    phase: str
    focus: Optional[str] = None
    target_tss: float
    target_hours: float
    total_planned_tss: float = 0.0
    total_planned_minutes: int = 0
    status: str
    notes: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class MicrocycleDetailResponse(MicrocycleSummaryResponse):
    workouts: List[PlannedWorkoutResponse] = []
    goal_name: Optional[str] = None
