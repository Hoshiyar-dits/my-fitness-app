from datetime import date
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from app.body_metrics.dto.BodyFatMethod import BodyFatMethod
from app.checkins.dto.WarningSymptom import WarningSymptom

class CreateCheckin(BaseModel):
    """Every measurement is optional. Weight / body fat are saved as that day's body metric."""
    model_config = ConfigDict(use_enum_values=True)

    checkin_date: date = Field(default_factory=date.today)
    sleep_hours: Optional[Decimal] = Field(default=None, ge=0, le=24, max_digits=3, decimal_places=1)
    sleep_quality: Optional[int] = Field(default=None, ge=1, le=5, description="1 very poor - 5 very good")
    energy_level: Optional[int] = Field(default=None, ge=1, le=5, description="1 very low - 5 very high")
    fatigue_level: Optional[int] = Field(default=None, ge=1, le=5, description="1 fresh - 5 exhausted")
    soreness_level: Optional[int] = Field(default=None, ge=1, le=5, description="1 none - 5 severe")
    pain_level: Optional[int] = Field(default=None, ge=0, le=10, description="0 none - 10 worst imaginable")
    pain_location: Optional[str] = Field(default=None, max_length=255)
    warning_symptoms: List[WarningSymptom] = Field(default_factory=list, max_length=10)
    workout_completed: Optional[bool] = None
    perceived_effort: Optional[int] = Field(default=None, ge=1, le=10)
    resting_heart_rate: Optional[int] = Field(default=None, ge=25, le=250)
    weight_kg: Optional[Decimal] = Field(default=None, gt=0, lt=1000, max_digits=5, decimal_places=2)
    body_fat_pct: Optional[Decimal] = Field(default=None, gt=0, lt=100, max_digits=4, decimal_places=1)
    body_fat_method: Optional[BodyFatMethod] = None
    notes: Optional[str] = Field(default=None, max_length=2000)

    @field_validator("checkin_date")
    def validate_checkin_date(cls, value):
        if value > date.today():
            raise ValueError("checkin_date cannot be in the future")
        return value

    @model_validator(mode="after")
    def validate_body_fat(self):
        if self.body_fat_method is not None and self.body_fat_pct is None:
            raise ValueError("body_fat_method given without body_fat_pct")
        return self
