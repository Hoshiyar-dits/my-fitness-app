from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, computed_field
from app.goals.dto.GoalEnums import TIMED_GOALS

class GoalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    program_id: Optional[int]
    goal_type: str
    title: Optional[str]
    unit: str
    reference_distance_m: Optional[Decimal]
    technique: Optional[str]
    start_date: date
    target_date: date
    baseline_value: Optional[Decimal]
    target_value: Decimal
    current_value: Optional[Decimal]
    current_value_date: Optional[date]
    status: str
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def lower_is_better(self) -> bool:
        if self.goal_type in TIMED_GOALS:
            return True
        if self.baseline_value is not None:
            return self.target_value < self.baseline_value
        return False

    @computed_field
    @property
    def progress_pct(self) -> Optional[float]:
        """Share of the baseline-to-target gap covered so far (can be negative or above 100)."""
        if self.baseline_value is None or self.current_value is None or self.target_value == self.baseline_value:
            return None
        return round(float((self.current_value - self.baseline_value) / (self.target_value - self.baseline_value)) * 100, 1)
