from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

class PlannedExerciseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    exercise_id: int
    exercise_name: str
    position: int
    sets: Optional[int]
    reps: Optional[int]
    distance_m: Optional[Decimal]
    duration_seconds: Optional[int]
    rest_seconds: Optional[int]
    effort: Optional[str]
    notes: Optional[str]

class PerformedExerciseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    exercise_id: int
    exercise_name: str
    sets: Optional[int]
    reps: Optional[int]
    distance_m: Optional[Decimal]
    duration_seconds: Optional[int]
    load_kg: Optional[Decimal]
    notes: Optional[str]

class PlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    program_id: Optional[int]
    plan_date: date
    day_number: Optional[int]
    training_phase: Optional[str]
    session_type: str
    title: str
    description: Optional[str]
    warm_up: Optional[str]
    cool_down: Optional[str]
    intensity: str
    estimated_duration_minutes: int
    is_high_impact: bool
    source: str
    status: str
    confirmed_at: Optional[datetime]
    adjustment_reason: Optional[str]
    based_on_plan_id: Optional[int]
    completion_status: str
    skip_reason: Optional[str]
    actual_duration_minutes: Optional[int]
    perceived_effort: Optional[int]
    completion_notes: Optional[str]
    completed_at: Optional[datetime]
    workout_id: Optional[int]
    exercises: List[PlannedExerciseResponse]
    performed_exercises: List[PerformedExerciseResponse]
    created_at: datetime
    updated_at: datetime
