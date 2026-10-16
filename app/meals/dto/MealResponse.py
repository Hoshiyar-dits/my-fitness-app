from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict

class MealResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    meal_date: date
    meal_type: str
    name: str
    calories: int
    protein_g: Optional[Decimal]
    carbs_g: Optional[Decimal]
    fat_g: Optional[Decimal]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
