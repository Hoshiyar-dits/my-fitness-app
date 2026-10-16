from datetime import date
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.meals.dto.MealType import MealType

class CreateMeal(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    meal_date: date = Field(default_factory=date.today)
    meal_type: MealType
    name: str = Field(min_length=1, max_length=255)
    calories: int = Field(ge=0, le=10000)
    protein_g: Optional[Decimal] = Field(default=None, ge=0, max_digits=6, decimal_places=2)
    carbs_g: Optional[Decimal] = Field(default=None, ge=0, max_digits=6, decimal_places=2)
    fat_g: Optional[Decimal] = Field(default=None, ge=0, max_digits=6, decimal_places=2)
    notes: Optional[str] = Field(default=None, max_length=2000)

    @field_validator("meal_date")
    def validate_meal_date(cls, value):
        if value > date.today():
            raise ValueError("meal_date cannot be in the future")
        return value
