from datetime import date, timedelta
from fastapi import Depends, HTTPException
from app.progress.repository import ProgressRepository
from app.progress.dto.DailySummary import DailySummary
from app.progress.dto.PeriodSummary import PeriodSummary
from app.progress.dto.PeriodTotals import PeriodTotals
from app.progress.dto.DashboardResponse import DashboardResponse

MAX_RANGE_DAYS = 92

def week_start(day: date) -> date:
    return day - timedelta(days=day.weekday())  # Monday

class ProgressService():
    def __init__(self, repository: ProgressRepository = Depends()):
        self.repository = repository

    def daily(self, user_id: int, day: date) -> DailySummary:
        return self._daily_summaries(user_id, day, day)[0]

    def weekly(self, user_id: int, any_day_in_week: date) -> PeriodSummary:
        start = week_start(any_day_in_week)
        return self.period(user_id, start, start + timedelta(days=6))

    def period(self, user_id: int, start: date, end: date) -> PeriodSummary:
        if end < start:
            raise HTTPException(status_code=422, detail="to_date must be on or after from_date")
        if (end - start).days + 1 > MAX_RANGE_DAYS:
            raise HTTPException(status_code=422, detail=f"Range cannot exceed {MAX_RANGE_DAYS} days")

        days = self._daily_summaries(user_id, start, end)
        meal_days = [d for d in days if d.meals_count]
        weights = [d.weight_kg for d in days if d.weight_kg is not None]
        start_weight = weights[0] if weights else None
        end_weight = weights[-1] if weights else None

        totals = PeriodTotals(
            workouts_count=sum(d.workouts_count for d in days),
            workout_minutes=sum(d.workout_minutes for d in days),
            calories_burned=sum(d.calories_burned for d in days),
            calories_consumed=sum(d.calories_consumed for d in days),
            protein_g=round(sum(d.protein_g for d in days), 1),
            carbs_g=round(sum(d.carbs_g for d in days), 1),
            fat_g=round(sum(d.fat_g for d in days), 1),
            active_days=sum(1 for d in days if d.workouts_count),
            days_with_meals_logged=len(meal_days),
            # averaged over days the user actually logged food, so unlogged days don't look like fasting
            avg_daily_calories_consumed=round(sum(d.calories_consumed for d in meal_days) / len(meal_days), 1) if meal_days else None,
            avg_daily_workout_minutes=round(sum(d.workout_minutes for d in days) / len(days), 1),
        )
        return PeriodSummary(
            start_date=start,
            end_date=end,
            totals=totals,
            start_weight_kg=start_weight,
            end_weight_kg=end_weight,
            weight_change_kg=round(end_weight - start_weight, 2) if len(weights) >= 2 else None,
            days=days,
        )

    def dashboard(self, user_id: int) -> DashboardResponse:
        today = date.today()
        latest = self.repository.latest_body_metric(user_id, today)
        return DashboardResponse(
            today=self.daily(user_id, today),
            this_week=self.weekly(user_id, today),
            last_week=self.weekly(user_id, today - timedelta(days=7)),
            latest_weight_kg=float(latest.weight_kg) if latest else None,
            latest_weight_date=latest.log_date if latest else None,
            workout_streak_days=self._workout_streak(user_id, today),
        )

    def _daily_summaries(self, user_id: int, start: date, end: date):
        days = {}
        current = start
        while current <= end:
            days[current] = DailySummary(date=current)
            current += timedelta(days=1)

        for row in self.repository.workout_totals_by_day(user_id, start, end):
            summary = days[row.day]
            summary.workouts_count = row.count
            summary.workout_minutes = int(row.minutes)
            summary.calories_burned = int(row.calories)

        for row in self.repository.meal_totals_by_day(user_id, start, end):
            summary = days[row.day]
            summary.meals_count = row.count
            summary.calories_consumed = int(row.calories)
            summary.protein_g = round(float(row.protein), 1)
            summary.carbs_g = round(float(row.carbs), 1)
            summary.fat_g = round(float(row.fat), 1)

        for log_date, weight in self.repository.weights_in_range(user_id, start, end):
            days[log_date].weight_kg = float(weight)

        for summary in days.values():
            summary.net_calories = summary.calories_consumed - summary.calories_burned
        return list(days.values())

    def _workout_streak(self, user_id: int, today: date) -> int:
        # consecutive days with a workout, ending today (or yesterday, so the streak isn't "broken" before the user trains today)
        dates = self.repository.recent_workout_dates(user_id, today)
        if not dates:
            return 0
        expected = today if dates[0] == today else today - timedelta(days=1)
        streak = 0
        for workout_date in dates:
            if workout_date != expected:
                break
            streak += 1
            expected -= timedelta(days=1)
        return streak
