from datetime import date
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, field_validator

class LogBodyMetric(BaseModel):
    log_date: date = Field(default_factory=date.today)
    weight_kg: Decimal = Field(gt=0, lt=1000, max_digits=5, decimal_places=2)
    body_fat_pct: Optional[Decimal] = Field(default=None, gt=0, lt=100, max_digits=4, decimal_places=1)

    @field_validator("log_date")
    def validate_log_date(cls, value):
        if value > date.today():
            raise ValueError("log_date cannot be in the future")
        return value
