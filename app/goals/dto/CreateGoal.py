from datetime import date
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.goals.dto.GoalEnums import GoalType, GOAL_UNITS, TIMED_GOALS, JUMP_GOALS

class CreateGoal(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    goal_type: GoalType
    title: Optional[str] = Field(default=None, max_length=255)
    unit: Optional[str] = Field(default=None, description="Must match the goal type: s, cm, kg or pct. Defaults to it.")
    reference_distance_m: Optional[Decimal] = Field(default=None, gt=0, le=100000, max_digits=9, decimal_places=2)
    technique: Optional[str] = Field(default=None, max_length=30)
    start_date: date = Field(default_factory=date.today)
    target_date: date
    baseline_value: Optional[Decimal] = Field(default=None, gt=0, max_digits=10, decimal_places=3)
    target_value: Decimal = Field(gt=0, max_digits=10, decimal_places=3)
    program_id: Optional[int] = None

    @model_validator(mode="after")
    def validate_goal(self):
        expected_unit = GOAL_UNITS[GoalType(self.goal_type)]
        if self.unit is None:
            self.unit = expected_unit
        elif self.unit != expected_unit:
            raise ValueError(f"{self.goal_type} goals are measured in '{expected_unit}', not '{self.unit}'")
        if self.goal_type in TIMED_GOALS and self.reference_distance_m is None:
            raise ValueError("reference_distance_m is required for timed goals (the distance the time refers to)")
        if self.goal_type not in TIMED_GOALS and self.reference_distance_m is not None:
            raise ValueError("reference_distance_m only applies to running_time and sprint_time goals")
        if self.technique is not None and self.goal_type not in JUMP_GOALS:
            raise ValueError("technique only applies to jump goals")
        if self.goal_type == GoalType.body_fat and (self.target_value >= 100 or (self.baseline_value or 0) >= 100):
            raise ValueError("body fat values are percentages below 100")
        if self.target_date <= self.start_date:
            raise ValueError("target_date must be after start_date")
        if (self.target_date - self.start_date).days > 366:
            raise ValueError("goals can span at most one year")
        if self.baseline_value is not None and self.baseline_value == self.target_value:
            raise ValueError("target_value must differ from baseline_value")
        return self
