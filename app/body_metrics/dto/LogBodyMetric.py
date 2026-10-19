from datetime import date
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from app.body_metrics.dto.BodyFatMethod import BodyFatMethod

class LogBodyMetric(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    log_date: date = Field(default_factory=date.today)
    weight_kg: Decimal = Field(gt=0, lt=1000, max_digits=5, decimal_places=2)
    body_fat_pct: Optional[Decimal] = Field(default=None, gt=0, lt=100, max_digits=4, decimal_places=1)
    body_fat_method: Optional[BodyFatMethod] = None

    @field_validator("log_date")
    def validate_log_date(cls, value):
        if value > date.today():
            raise ValueError("log_date cannot be in the future")
        return value

    @model_validator(mode="after")
    def validate_body_fat_method(self):
        if self.body_fat_method is not None and self.body_fat_pct is None:
            raise ValueError("body_fat_method given without body_fat_pct")
        return self
