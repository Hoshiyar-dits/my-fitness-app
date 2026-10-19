from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field

class PlannedExerciseInput(BaseModel):
    exercise_id: int
    sets: Optional[int] = Field(default=None, ge=1, le=50)
    reps: Optional[int] = Field(default=None, ge=1, le=500)
    distance_m: Optional[Decimal] = Field(default=None, gt=0, le=100000, max_digits=9, decimal_places=2)
    duration_seconds: Optional[int] = Field(default=None, gt=0, le=86400)
    rest_seconds: Optional[int] = Field(default=None, ge=0, le=3600)
    effort: Optional[str] = Field(default=None, max_length=100)
    notes: Optional[str] = Field(default=None, max_length=1000)

class PerformedExerciseInput(BaseModel):
    exercise_id: int
    sets: Optional[int] = Field(default=None, ge=1, le=50)
    reps: Optional[int] = Field(default=None, ge=1, le=500)
    distance_m: Optional[Decimal] = Field(default=None, gt=0, le=100000, max_digits=9, decimal_places=2)
    duration_seconds: Optional[int] = Field(default=None, gt=0, le=86400)
    load_kg: Optional[Decimal] = Field(default=None, ge=0, le=1000, max_digits=6, decimal_places=2)
    notes: Optional[str] = Field(default=None, max_length=1000)
