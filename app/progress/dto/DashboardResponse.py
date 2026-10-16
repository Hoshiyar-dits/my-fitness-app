from datetime import date
from typing import Optional
from pydantic import BaseModel
from app.progress.dto.DailySummary import DailySummary
from app.progress.dto.PeriodSummary import PeriodSummary

class DashboardResponse(BaseModel):
    today: DailySummary
    this_week: PeriodSummary
    last_week: PeriodSummary
    latest_weight_kg: Optional[float]
    latest_weight_date: Optional[date]
    workout_streak_days: int
