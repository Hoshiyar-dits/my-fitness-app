from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends
from app.auth.dependencies import get_current_user
from app.progress.dto.DailySummary import DailySummary
from app.progress.dto.PeriodSummary import PeriodSummary
from app.progress.dto.DashboardResponse import DashboardResponse
from app.progress.service import ProgressService
from app.progress.training_service import TrainingProgressService
from app.progress.dto.TrainingSummary import ProgramProgress, WeeklyProgress

router = APIRouter(tags=['progress'])

@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(current_user = Depends(get_current_user), service: ProgressService = Depends()):
    return service.dashboard(current_user.id)

@router.get("/progress/daily", response_model=DailySummary)
def daily_progress(day: Optional[date] = None, current_user = Depends(get_current_user), service: ProgressService = Depends()):
    return service.daily(current_user.id, day or date.today())

@router.get("/progress/weekly", response_model=WeeklyProgress)
def weekly_progress(
    week_of: Optional[date] = None,
    current_user = Depends(get_current_user),
    service: TrainingProgressService = Depends(),
):
    """Monday–Sunday week containing `week_of` (defaults to the current week), with training adherence and performance."""
    return service.weekly(current_user.id, week_of or date.today())

@router.get("/progress/25-day", response_model=ProgramProgress)
def program_progress(program_id: Optional[int] = None, current_user = Depends(get_current_user), service: TrainingProgressService = Depends()):
    """Progress over the current (or given) 25-day program: adherence, assessments vs baseline, body trends, goals."""
    return service.program_report(current_user.id, program_id)

@router.get("/progress/range", response_model=PeriodSummary)
def range_progress(from_date: date, to_date: date, current_user = Depends(get_current_user), service: ProgressService = Depends()):
    return service.period(current_user.id, from_date, to_date)
