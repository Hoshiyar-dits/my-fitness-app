from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends
from app.auth.dependencies import get_current_user
from app.progress.dto.DailySummary import DailySummary
from app.progress.dto.PeriodSummary import PeriodSummary
from app.progress.dto.DashboardResponse import DashboardResponse
from app.progress.service import ProgressService

router = APIRouter(tags=['progress'])

@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(current_user = Depends(get_current_user), service: ProgressService = Depends()):
    return service.dashboard(current_user.id)

@router.get("/progress/daily", response_model=DailySummary)
def daily_progress(day: Optional[date] = None, current_user = Depends(get_current_user), service: ProgressService = Depends()):
    return service.daily(current_user.id, day or date.today())

@router.get("/progress/weekly", response_model=PeriodSummary)
def weekly_progress(
    week_of: Optional[date] = None,
    current_user = Depends(get_current_user),
    service: ProgressService = Depends(),
):
    """Monday–Sunday week containing `week_of` (defaults to the current week)."""
    return service.weekly(current_user.id, week_of or date.today())

@router.get("/progress/range", response_model=PeriodSummary)
def range_progress(from_date: date, to_date: date, current_user = Depends(get_current_user), service: ProgressService = Depends()):
    return service.period(current_user.id, from_date, to_date)
