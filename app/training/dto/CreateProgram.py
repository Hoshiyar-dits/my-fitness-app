from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from app.training.dto.TrainingEnums import ExperienceLevel, Equipment
from app.body_metrics.dto.BodyFatMethod import BodyFatMethod

class BaselineMeasurements(BaseModel):
    """What the user currently knows about their performance. Every field is optional.
    Saved as self-reported measurements; the day-1 and day-3 assessments give the standardized baseline."""
    model_config = ConfigDict(use_enum_values=True)

    run_distance_m: Optional[Decimal] = Field(default=None, gt=0, le=100000, max_digits=9, decimal_places=2)
    run_elapsed_seconds: Optional[Decimal] = Field(default=None, gt=0, le=86400, max_digits=9, decimal_places=2)
    sprint_distance_m: Optional[Decimal] = Field(default=None, gt=0, le=400, max_digits=9, decimal_places=2)
    sprint_elapsed_seconds: Optional[Decimal] = Field(default=None, gt=0, le=600, max_digits=9, decimal_places=2)
    long_jump_cm: Optional[Decimal] = Field(default=None, gt=0, le=1000, max_digits=6, decimal_places=1)
    long_jump_technique: Optional[str] = Field(default="standing", max_length=30)
    high_jump_cm: Optional[Decimal] = Field(default=None, gt=0, le=300, max_digits=6, decimal_places=1)
    high_jump_technique: Optional[str] = Field(default=None, max_length=30)
    weight_kg: Optional[Decimal] = Field(default=None, gt=0, lt=1000, max_digits=5, decimal_places=2)
    body_fat_pct: Optional[Decimal] = Field(default=None, gt=0, lt=100, max_digits=4, decimal_places=1)
    body_fat_method: Optional[BodyFatMethod] = None

    @model_validator(mode="after")
    def validate_pairs(self):
        if (self.run_distance_m is None) != (self.run_elapsed_seconds is None):
            raise ValueError("give both run_distance_m and run_elapsed_seconds, or neither")
        if (self.sprint_distance_m is None) != (self.sprint_elapsed_seconds is None):
            raise ValueError("give both sprint_distance_m and sprint_elapsed_seconds, or neither")
        if self.body_fat_pct is not None and self.weight_kg is None:
            raise ValueError("body_fat_pct is stored with a weigh-in, so weight_kg is required too")
        return self

class ProgramTargets(BaseModel):
    """Optional targets agreed with the user. Each one creates a goal for the program's 25 days."""
    run_elapsed_seconds: Optional[Decimal] = Field(default=None, gt=0, le=86400, max_digits=10, decimal_places=3)
    sprint_elapsed_seconds: Optional[Decimal] = Field(default=None, gt=0, le=600, max_digits=10, decimal_places=3)
    long_jump_cm: Optional[Decimal] = Field(default=None, gt=0, le=1000, max_digits=10, decimal_places=3)
    high_jump_cm: Optional[Decimal] = Field(default=None, gt=0, le=300, max_digits=10, decimal_places=3)
    weight_kg: Optional[Decimal] = Field(default=None, gt=0, lt=1000, max_digits=10, decimal_places=3)
    body_fat_pct: Optional[Decimal] = Field(default=None, gt=0, lt=100, max_digits=10, decimal_places=3)

class CreateProgram(BaseModel):
    """Initial assessment. Age comes from the user profile (POST /user/profile)."""
    model_config = ConfigDict(use_enum_values=True)

    start_date: date = Field(default_factory=date.today)
    experience_level: ExperienceLevel
    training_background: Optional[str] = Field(default=None, max_length=2000)
    available_minutes_per_day: int = Field(ge=15, le=240)
    equipment: List[Equipment] = Field(default_factory=list, max_length=10)
    injury_history: Optional[str] = Field(default=None, max_length=2000)
    current_pain: Optional[str] = Field(default=None, max_length=2000, description="Any pain or discomfort right now")
    medical_restrictions: Optional[str] = Field(default=None, max_length=2000)
    medical_clearance_confirmed: bool = Field(
        default=False, description="True if a healthcare professional has cleared you for strenuous training",
    )
    assessment_run_distance_m: Optional[Decimal] = Field(default=None, ge=400, le=21100, max_digits=9, decimal_places=2)
    assessment_sprint_distance_m: Optional[Decimal] = Field(default=None, ge=10, le=100, max_digits=6, decimal_places=2)
    baseline: Optional[BaselineMeasurements] = None
    targets: Optional[ProgramTargets] = None
    notes: Optional[str] = Field(default=None, max_length=2000)

    @field_validator("start_date")
    def validate_start_date(cls, value):
        if value < date.today():
            raise ValueError("start_date cannot be in the past")
        if value > date.today() + timedelta(days=30):
            raise ValueError("start_date must be within the next 30 days")
        return value

    @field_validator("injury_history", "current_pain", "medical_restrictions", "training_background", "notes")
    def blank_to_none(cls, value):
        return (value.strip() or None) if value is not None else None
