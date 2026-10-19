from typing import List, Literal, Optional
from pydantic import BaseModel, Field
from app.training.dto.PlannedExerciseInput import PerformedExerciseInput
from app.activities.dto.CreateActivity import CreateActivity

class CompletePlan(BaseModel):
    completion_status: Literal["completed", "partial"] = "completed"
    actual_duration_minutes: int = Field(gt=0, le=1440)
    perceived_effort: Optional[int] = Field(default=None, ge=1, le=10, description="RPE, 1 (very easy) to 10 (maximal)")
    calories_burned: Optional[int] = Field(default=None, ge=0, le=10000)
    notes: Optional[str] = Field(default=None, max_length=2000)
    performed_exercises: List[PerformedExerciseInput] = Field(default_factory=list, max_length=50)
    activities: List[CreateActivity] = Field(default_factory=list, max_length=50, description="Measured runs, sprints and jumps")

class SkipPlan(BaseModel):
    reason: str = Field(min_length=1, max_length=1000)
