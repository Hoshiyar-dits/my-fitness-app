from datetime import date, timedelta
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.training.dto.TrainingEnums import SessionType
from app.training.dto.PlannedExerciseInput import PlannedExerciseInput
from app.workouts.dto.WorkoutEnums import Intensity

class CreatePlan(BaseModel):
    """A session the user plans themselves. Saved as confirmed, with source 'user'."""
    model_config = ConfigDict(use_enum_values=True)

    plan_date: date
    session_type: SessionType
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=4000)
    intensity: Intensity = Intensity.moderate
    estimated_duration_minutes: int = Field(ge=0, le=600)
    exercises: List[PlannedExerciseInput] = Field(default_factory=list, max_length=30)

    @field_validator("plan_date")
    def validate_plan_date(cls, value):
        if value < date.today() - timedelta(days=7) or value > date.today() + timedelta(days=60):
            raise ValueError("plan_date must be between 7 days ago and 60 days ahead")
        return value
