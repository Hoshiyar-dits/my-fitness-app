from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, computed_field
from app.analysis.readiness import safety_alert
from app.body_metrics.dto.BodyMetricResponse import BodyMetricResponse

class CheckinResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    checkin_date: date
    sleep_hours: Optional[Decimal]
    sleep_quality: Optional[int]
    energy_level: Optional[int]
    fatigue_level: Optional[int]
    soreness_level: Optional[int]
    pain_level: Optional[int]
    pain_location: Optional[str]
    warning_symptoms: List[str]
    workout_completed: Optional[bool]
    perceived_effort: Optional[int]
    resting_heart_rate: Optional[int]
    notes: Optional[str]
    body_metric: Optional[BodyMetricResponse] = None
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def safety_alert(self) -> Optional[str]:
        return safety_alert(self.warning_symptoms, self.pain_level)
