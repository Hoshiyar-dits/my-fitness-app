from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, computed_field
from app.activities.metrics import pace_seconds_per_km, speed_m_per_s

class SplitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    split_number: int
    distance_m: Decimal
    elapsed_seconds: Decimal

    @computed_field
    @property
    def pace_seconds_per_km(self) -> Optional[float]:
        return pace_seconds_per_km(self.distance_m, self.elapsed_seconds)

class ActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    activity_date: date
    activity_type: str
    distance_m: Optional[Decimal]
    elapsed_seconds: Optional[Decimal]
    jump_cm: Optional[Decimal]
    technique: Optional[str]
    attempt_number: Optional[int]
    is_assessment: bool
    measurement_method: Optional[str]
    conditions: Optional[str]
    perceived_effort: Optional[int]
    planned_workout_id: Optional[int]
    notes: Optional[str]
    splits: List[SplitResponse]
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def pace_seconds_per_km(self) -> Optional[float]:
        return pace_seconds_per_km(self.distance_m, self.elapsed_seconds)

    @computed_field
    @property
    def speed_m_per_s(self) -> Optional[float]:
        return speed_m_per_s(self.distance_m, self.elapsed_seconds)
