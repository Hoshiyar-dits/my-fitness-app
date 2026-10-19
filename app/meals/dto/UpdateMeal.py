from datetime import date, time
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.meals.dto.MealType import MealType
from app.meals.dto.NutritionAccuracy import NutritionAccuracy

class UpdateMeal(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    meal_date: Optional[date] = None
    meal_type: Optional[MealType] = None
    meal_time: Optional[time] = None
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    calories: Optional[int] = Field(default=None, ge=0, le=10000)
    protein_g: Optional[Decimal] = Field(default=None, ge=0, max_digits=6, decimal_places=2)
    carbs_g: Optional[Decimal] = Field(default=None, ge=0, max_digits=6, decimal_places=2)
    fat_g: Optional[Decimal] = Field(default=None, ge=0, max_digits=6, decimal_places=2)
    nutrition_accuracy: Optional[NutritionAccuracy] = None
    nutrition_source: Optional[str] = Field(default=None, max_length=100)
    notes: Optional[str] = Field(default=None, max_length=2000)

    @field_validator("meal_date")
    def validate_meal_date(cls, value):
        if value is not None and value > date.today():
            raise ValueError("meal_date cannot be in the future")
        return value
