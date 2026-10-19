from datetime import date, datetime, time
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict

class MealResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    meal_date: date
    meal_type: str
    meal_time: Optional[time]
    name: str
    calories: int
    protein_g: Optional[Decimal]
    carbs_g: Optional[Decimal]
    fat_g: Optional[Decimal]
    nutrition_accuracy: str
    nutrition_source: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
