from datetime import date
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from app.users.dto.ActivityLevel import ActivityLevel

class CreateUserProfile(BaseModel):
    date_of_birth: date
    height_cm: Decimal = Field(gt=0, le=300, max_digits=5, decimal_places=2)
    gender: Optional[str] = Field(default=None, max_length=30)
    activity_level: ActivityLevel

    @field_validator("date_of_birth")
    def validate_date_of_birth(cls, value):
        if value >= date.today():
            raise ValueError("date_of_birth must be in the past")
        return value
