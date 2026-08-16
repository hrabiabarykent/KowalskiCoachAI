from typing import List, Optional, Dict, Any
import re
from pydantic import BaseModel, Field, field_validator

class Step(BaseModel):
    duration_min: float = Field(..., gt=0, description="Czas trwania kroku w minutach (> 0)")
    target: str = Field(..., description="Target strefowy np. 60% HR, Z2, 200W")
    label: Optional[str] = Field(None, description="Etykieta opcjonalna np. Rozgrzewka")

    @field_validator("target")
    @classmethod
    def validate_target(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Target strefowy nie może być pusty.")
        return v.strip()


class RepeatBlock(BaseModel):
    reps: int = Field(1, ge=1, description="Liczba powtórzeń bloku (>= 1)")
    steps: List[Step] = Field(..., min_length=1, description="Lista kroków (min. 1 krok)")


class StructuredWorkout(BaseModel):
    name: str = Field(..., description="Nazwa ustrukturyzowanego treningu")
    blocks: List[RepeatBlock] = Field(..., min_length=1, description="Bloki powtórzeniowe (min. 1 blok)")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Nazwa treningu nie może być pusta.")
        return v.strip()


def build_intervals_dsl(workout: StructuredWorkout) -> str:
    """
    Przekształca walidowany obiekt StructuredWorkout w bezbłędny,
    deterministyczny tekst w formacie Intervals.icu Workout DSL.
    """
    lines = []
    for b in workout.blocks:
        if b.reps > 1:
            lines.append("")
            lines.append(f"{b.reps}x")
            for s in b.steps:
                secs = round(s.duration_min * 60)
                dur = f"{int(s.duration_min)}m" if (s.duration_min >= 1 and secs % 60 == 0) else f"{secs}s"
                lbl = f" {s.label}" if s.label else ""
                lines.append(f"  - {dur} {s.target}{lbl}".rstrip())
            lines.append("")
        else:
            for s in b.steps:
                secs = round(s.duration_min * 60)
                dur = f"{int(s.duration_min)}m" if (s.duration_min >= 1 and secs % 60 == 0) else f"{secs}s"
                lbl = f" {s.label}" if s.label else ""
                lines.append(f"- {dur} {s.target}{lbl}".rstrip())

    result = "\n".join(lines)
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()


def build_event_payload(
    date_iso: str,
    workout_name: str,
    workout_type: str,
    planned_tss: float,
    moving_min: float,
    dsl_text: str,
    tag: str = "[Kowalski]"
) -> Dict[str, Any]:
    """
    Tworzy poprawny słownik payload do wysłania do API Intervals.icu.
    """
    clean_name = f"{tag} {workout_name}" if not workout_name.startswith(tag) else workout_name
    tagged_desc = f"{tag}\n{dsl_text}".strip() if dsl_text else tag
    moving_sec = int(round(moving_min * 60))

    return {
        "category": "WORKOUT",
        "start_date_local": f"{date_iso}T07:00:00",
        "name": clean_name,
        "type": workout_type,
        "icu_training_load": int(round(planned_tss)),
        "moving_time": moving_sec,
        "description": tagged_desc
    }
