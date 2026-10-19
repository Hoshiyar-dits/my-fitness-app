from datetime import date
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.workouts.dto.WorkoutEnums import Intensity

class UpdatePlan(BaseModel):
    """status: confirm or reject a proposed plan. Other fields can only change while the plan is pending."""
    model_config = ConfigDict(use_enum_values=True)

    status: Optional[Literal["confirmed", "rejected"]] = None
    plan_date: Optional[date] = None
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=4000)
    intensity: Optional[Intensity] = None
    estimated_duration_minutes: Optional[int] = Field(default=None, ge=0, le=600)
