from typing import Optional
from pydantic import BaseModel

class PeriodTotals(BaseModel):
    workouts_count: int
    workout_minutes: int
    calories_burned: int
    calories_consumed: int
    protein_g: float
    carbs_g: float
    fat_g: float
    active_days: int
    days_with_meals_logged: int
    avg_daily_calories_consumed: Optional[float]
    avg_daily_workout_minutes: float
