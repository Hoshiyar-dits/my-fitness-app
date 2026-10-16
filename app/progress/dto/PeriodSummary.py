from datetime import date
from typing import List, Optional
from pydantic import BaseModel
from app.progress.dto.DailySummary import DailySummary
from app.progress.dto.PeriodTotals import PeriodTotals

class PeriodSummary(BaseModel):
    start_date: date
    end_date: date
    totals: PeriodTotals
    start_weight_kg: Optional[float]
    end_weight_kg: Optional[float]
    weight_change_kg: Optional[float]
    days: List[DailySummary]
