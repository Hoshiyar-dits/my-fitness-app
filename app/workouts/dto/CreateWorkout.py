from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.workouts.dto.WorkoutEnums import WorkoutType, Intensity

class CreateWorkout(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    workout_date: date = Field(default_factory=date.today)
    workout_type: WorkoutType
    name: str = Field(min_length=1, max_length=255)
    duration_minutes: int = Field(gt=0, le=1440)
    calories_burned: Optional[int] = Field(default=None, ge=0, le=10000)
    intensity: Optional[Intensity] = None
    notes: Optional[str] = Field(default=None, max_length=2000)

    @field_validator("workout_date")
    def validate_workout_date(cls, value):
        if value > date.today():
            raise ValueError("workout_date cannot be in the future")
        return value
