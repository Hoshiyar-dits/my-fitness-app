from datetime import date
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.goals.dto.GoalEnums import GoalStatus

class UpdateGoal(BaseModel):
    """goal_type, unit and reference distance are fixed after creation so stored values stay comparable."""
    model_config = ConfigDict(use_enum_values=True)

    title: Optional[str] = Field(default=None, max_length=255)
    target_date: Optional[date] = None
    baseline_value: Optional[Decimal] = Field(default=None, gt=0, max_digits=10, decimal_places=3)
    target_value: Optional[Decimal] = Field(default=None, gt=0, max_digits=10, decimal_places=3)
    current_value: Optional[Decimal] = Field(default=None, gt=0, max_digits=10, decimal_places=3)
    current_value_date: Optional[date] = None
    status: Optional[GoalStatus] = None
