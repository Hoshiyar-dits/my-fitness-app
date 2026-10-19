from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.body_metrics.dto.BodyFatMethod import BodyFatMethod
from app.checkins.dto.WarningSymptom import WarningSymptom

class UpdateCheckin(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    sleep_hours: Optional[Decimal] = Field(default=None, ge=0, le=24, max_digits=3, decimal_places=1)
    sleep_quality: Optional[int] = Field(default=None, ge=1, le=5)
    energy_level: Optional[int] = Field(default=None, ge=1, le=5)
    fatigue_level: Optional[int] = Field(default=None, ge=1, le=5)
    soreness_level: Optional[int] = Field(default=None, ge=1, le=5)
    pain_level: Optional[int] = Field(default=None, ge=0, le=10)
    pain_location: Optional[str] = Field(default=None, max_length=255)
    warning_symptoms: Optional[List[WarningSymptom]] = Field(default=None, max_length=10)
    workout_completed: Optional[bool] = None
    perceived_effort: Optional[int] = Field(default=None, ge=1, le=10)
    resting_heart_rate: Optional[int] = Field(default=None, ge=25, le=250)
    weight_kg: Optional[Decimal] = Field(default=None, gt=0, lt=1000, max_digits=5, decimal_places=2)
    body_fat_pct: Optional[Decimal] = Field(default=None, gt=0, lt=100, max_digits=4, decimal_places=1)
    body_fat_method: Optional[BodyFatMethod] = None
    notes: Optional[str] = Field(default=None, max_length=2000)
