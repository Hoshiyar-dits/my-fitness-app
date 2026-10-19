from datetime import date
from typing import List, Optional
from pydantic import BaseModel
from app.progress.dto.PeriodSummary import PeriodSummary
from app.progress.dto.PerformanceComparison import PerformanceComparison, MeasurementTrend
from app.goals.dto.GoalResponse import GoalResponse

class SkippedSession(BaseModel):
    plan_id: int
    plan_date: date
    title: str
    reason: Optional[str]

class Adherence(BaseModel):
    planned_sessions: int  # confirmed, non-rest sessions up to and including the end date
    completed: int
    partial: int
    skipped: int
    not_logged: int
    completion_rate_pct: Optional[float]
    skipped_sessions: List[SkippedSession]

class CheckinAverages(BaseModel):
    checkins: int
    avg_sleep_hours: Optional[float]
    avg_energy: Optional[float]
    avg_fatigue: Optional[float]
    avg_soreness: Optional[float]
    days_with_pain: int
    days_with_warning_symptoms: int

class TrainingWeekSummary(BaseModel):
    adherence: Adherence
    high_impact_sessions_completed: int
    avg_perceived_effort: Optional[float]
    checkins: CheckinAverages
    performance: List[PerformanceComparison]

class WeeklyProgress(PeriodSummary):
    training: TrainingWeekSummary

class ProgramProgress(BaseModel):
    program_id: int
    status: str
    start_date: date
    end_date: date
    day_number: int  # 1-25; 0 before the start
    days_remaining: int
    adherence: Adherence
    checkins: CheckinAverages
    running: PerformanceComparison
    sprint: PerformanceComparison
    long_jump: PerformanceComparison
    high_jump: PerformanceComparison
    body_weight: MeasurementTrend
    body_fat: MeasurementTrend
    goals: List[GoalResponse]
    next_assessments: List[date]
    notes: List[str]
