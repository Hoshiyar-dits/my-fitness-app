from datetime import date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from app.auth.dependencies import get_current_user
from app.analysis.dto.DailyAnalysisResponse import DailyAnalysisResponse
from app.analysis.service import AnalysisService

router = APIRouter(prefix="/analysis", tags=['analysis'])

@router.get("/daily", response_model=DailyAnalysisResponse)
def daily_analysis(day: Optional[date] = None, current_user = Depends(get_current_user), service: AnalysisService = Depends()):
    """Reviews the day from the stored data. Idempotent: re-running it refreshes the saved analysis for that date."""
    day = day or date.today()
    if day > date.today() or day < date.today() - timedelta(days=90):
        raise HTTPException(status_code=422, detail="day must be within the last 90 days")
    return service.daily(current_user.id, day)
