from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class WorkoutResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workout_date: date
    workout_type: str
    name: str
    duration_minutes: int
    calories_burned: Optional[int]
    intensity: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
