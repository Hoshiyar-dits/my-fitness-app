from datetime import date
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from app.activities.dto.ActivityEnums import ActivityType, MeasurementMethod, JumpTechnique

TIMED_TYPES = ("run", "sprint")

class CreateSplit(BaseModel):
    """One segment: its own distance and time (not cumulative)."""
    distance_m: Decimal = Field(gt=0, le=100000, max_digits=9, decimal_places=2)
    elapsed_seconds: Decimal = Field(gt=0, le=86400, max_digits=9, decimal_places=2)

class CreateActivity(BaseModel):
    """Runs and sprints need distance_m + elapsed_seconds; jumps need jump_cm (distance for long jump,
    bar height cleared for high jump). Log each jump attempt separately."""
    model_config = ConfigDict(use_enum_values=True)

    activity_date: date = Field(default_factory=date.today)
    activity_type: ActivityType
    distance_m: Optional[Decimal] = Field(default=None, gt=0, le=100000, max_digits=9, decimal_places=2)
    elapsed_seconds: Optional[Decimal] = Field(default=None, gt=0, le=86400, max_digits=9, decimal_places=2)
    jump_cm: Optional[Decimal] = Field(default=None, gt=0, le=1000, max_digits=6, decimal_places=1)
    technique: Optional[JumpTechnique] = None
    attempt_number: Optional[int] = Field(default=None, ge=1, le=50)
    is_assessment: bool = False
    measurement_method: Optional[MeasurementMethod] = None
    conditions: Optional[str] = Field(default=None, max_length=255, description="e.g. surface, wind, temperature")
    perceived_effort: Optional[int] = Field(default=None, ge=1, le=10)
    planned_workout_id: Optional[int] = None
    notes: Optional[str] = Field(default=None, max_length=2000)
    splits: List[CreateSplit] = Field(default_factory=list, max_length=200)

    @field_validator("activity_date")
    def validate_activity_date(cls, value):
        if value > date.today():
            raise ValueError("activity_date cannot be in the future")
        return value

    @model_validator(mode="after")
    def validate_measurement(self):
        if self.activity_type in TIMED_TYPES:
            if self.distance_m is None or self.elapsed_seconds is None:
                raise ValueError(f"{self.activity_type} requires distance_m and elapsed_seconds")
            if self.jump_cm is not None or self.technique is not None:
                raise ValueError("jump_cm and technique only apply to jumps")
            if self.splits:
                # small tolerance for rounding in watch/app exports
                if sum(s.distance_m for s in self.splits) > self.distance_m * Decimal("1.01"):
                    raise ValueError("split distances add up to more than distance_m")
                if sum(s.elapsed_seconds for s in self.splits) > self.elapsed_seconds * Decimal("1.01"):
                    raise ValueError("split times add up to more than elapsed_seconds")
        else:
            if self.jump_cm is None:
                raise ValueError(f"{self.activity_type} requires jump_cm")
            if self.distance_m is not None or self.elapsed_seconds is not None or self.splits:
                raise ValueError("distance_m, elapsed_seconds and splits only apply to runs and sprints")
            if self.activity_type == "high_jump" and self.jump_cm > 300:
                raise ValueError("high jump height must be at most 300 cm")
        return self
