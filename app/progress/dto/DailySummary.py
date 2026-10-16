from datetime import date
from typing import Optional
from pydantic import BaseModel

class DailySummary(BaseModel):
    date: date
    workouts_count: int = 0
    workout_minutes: int = 0
    calories_burned: int = 0
    meals_count: int = 0
    calories_consumed: int = 0
    protein_g: float = 0
    carbs_g: float = 0
    fat_g: float = 0
    net_calories: int = 0
    weight_kg: Optional[float] = None
