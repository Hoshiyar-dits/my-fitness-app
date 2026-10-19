from datetime import date, timedelta
from typing import Optional
from fastapi import Depends, HTTPException
from app.activities.metrics import measurement_trend, performance_comparison
from app.activities.repository import ActivityRepository
from app.body_metrics.repository import BodyMetricRepository
from app.checkins.repository import CheckinRepository
from app.goals.repository import GoalRepository
from app.progress.service import ProgressService, week_start
from app.progress.dto.TrainingSummary import ProgramProgress, TrainingWeekSummary, WeeklyProgress
from app.training.repository import PlanRepository, ProgramRepository

COMPARISON_WINDOW_DAYS = 60


class TrainingProgressService():
    def __init__(
        self,
        progress: ProgressService = Depends(),
        plans: PlanRepository = Depends(),
        programs: ProgramRepository = Depends(),
        activities: ActivityRepository = Depends(),
        checkins: CheckinRepository = Depends(),
        body_metrics: BodyMetricRepository = Depends(),
        goals: GoalRepository = Depends(),
    ):
        self.progress = progress
        self.plans = plans
        self.programs = programs
        self.activities = activities
        self.checkins = checkins
        self.body_metrics = body_metrics
        self.goals = goals

    def weekly(self, user_id: int, any_day_in_week: date) -> WeeklyProgress:
        start = week_start(any_day_in_week)
        end = start + timedelta(days=6)
        period = self.progress.period(user_id, start, end)
        plans = self.plans.list(user_id, start, end, ["confirmed"])
        done = [p for p in plans if p.completion_status in ("completed", "partial")]
        efforts = [p.perceived_effort for p in done if p.perceived_effort is not None]

        week_activities = self.activities.list(user_id, None, start, end)
        history = self.activities.list(user_id, None, end - timedelta(days=COMPARISON_WINDOW_DAYS), end)
        performance = []
        for kind in ("run", "sprint", "long_jump", "high_jump"):
            latest = next((a for a in week_activities if a.activity_type == kind), None)  # list is newest first
            if latest is None:
                continue
            if kind in ("run", "sprint"):
                performance.append(performance_comparison(history, kind, reference_distance_m=latest.distance_m))
            else:
                performance.append(performance_comparison(history, kind, technique=latest.technique))

        training = TrainingWeekSummary(
            adherence=_adherence(plans),
            high_impact_sessions_completed=sum(1 for p in done if p.is_high_impact),
            avg_perceived_effort=round(sum(efforts) / len(efforts), 1) if efforts else None,
            checkins=_checkin_averages(self.checkins.list(user_id, start, end)),
            performance=performance,
        )
        return WeeklyProgress(**period.model_dump(), training=training)

    def program_report(self, user_id: int, program_id: Optional[int] = None) -> ProgramProgress:
        program = self.programs.get(user_id, program_id) if program_id else self.programs.current(user_id)
        if not program:
            raise HTTPException(status_code=404, detail="No training program found")
        today = date.today()
        # onboarding baseline measurements are dated the day the program was created
        window_start = min(program.start_date, program.created_at.date())
        window_end = min(program.end_date, today)

        plans = [p for p in self.plans.for_program(program.id) if p.status == "confirmed"]
        activities = self.activities.list(user_id, None, window_start, window_end)
        metrics = self.body_metrics.list(user_id, window_start, window_end, 366)

        body_fat_readings = [m for m in metrics if m.body_fat_pct is not None]
        latest_method = body_fat_readings[0].body_fat_method if body_fat_readings else None  # list is newest first
        body_fat = measurement_trend([(m.log_date, m.body_fat_pct) for m in body_fat_readings if m.body_fat_method == latest_method], "body_fat")
        body_fat["method"] = latest_method

        day_number = (today - program.start_date).days + 1
        notes = [
            "Assessment results are only compared with measurements taken the same way (same distance, technique and timing method).",
            "Weight and body fat are shown as trends of several readings. Single readings vary day to day.",
        ]
        if program.status == "awaiting_clearance":
            notes.append("This program is waiting for medical clearance, so no sessions have been scheduled yet.")

        return ProgramProgress(
            program_id=program.id,
            status=program.status,
            start_date=program.start_date,
            end_date=program.end_date,
            day_number=max(0, min(day_number, (program.end_date - program.start_date).days + 1)),
            days_remaining=max(0, (program.end_date - today).days),
            adherence=_adherence([p for p in plans if p.plan_date <= today]),
            checkins=_checkin_averages(self.checkins.list(user_id, program.start_date, window_end)),
            running=performance_comparison(activities, "run", reference_distance_m=program.assessment_run_distance_m),
            sprint=performance_comparison(activities, "sprint", reference_distance_m=program.assessment_sprint_distance_m),
            long_jump=performance_comparison(activities, "long_jump", technique="standing"),
            high_jump=performance_comparison(activities, "high_jump"),
            body_weight=measurement_trend([(m.log_date, m.weight_kg) for m in metrics], "body_weight"),
            body_fat=body_fat,
            goals=[g for g in self.goals.list(user_id, None, 200, 0) if g.program_id == program.id],
            next_assessments=[p.plan_date for p in plans
                              if p.session_type == "assessment" and p.plan_date >= today and p.completion_status == "pending"],
            notes=notes,
        )


def _adherence(plans) -> dict:
    today = date.today()
    training = [p for p in plans if p.session_type != "rest"]
    completed = [p for p in training if p.completion_status == "completed"]
    partial = [p for p in training if p.completion_status == "partial"]
    skipped = [p for p in training if p.completion_status == "skipped"]
    # sessions still pending today are not counted against the user yet
    not_logged = [p for p in training if p.completion_status == "pending" and p.plan_date < today]
    due = len(completed) + len(partial) + len(skipped) + len(not_logged)
    return {
        "planned_sessions": due,
        "completed": len(completed),
        "partial": len(partial),
        "skipped": len(skipped),
        "not_logged": len(not_logged),
        "completion_rate_pct": round((len(completed) + len(partial)) / due * 100, 1) if due else None,
        "skipped_sessions": [{"plan_id": p.id, "plan_date": p.plan_date, "title": p.title, "reason": p.skip_reason} for p in skipped],
    }


def _avg(values) -> Optional[float]:
    values = [float(v) for v in values if v is not None]
    return round(sum(values) / len(values), 1) if values else None


def _checkin_averages(checkins) -> dict:
    return {
        "checkins": len(checkins),
        "avg_sleep_hours": _avg(c.sleep_hours for c in checkins),
        "avg_energy": _avg(c.energy_level for c in checkins),
        "avg_fatigue": _avg(c.fatigue_level for c in checkins),
        "avg_soreness": _avg(c.soreness_level for c in checkins),
        "days_with_pain": sum(1 for c in checkins if c.pain_level),
        "days_with_warning_symptoms": sum(1 for c in checkins if c.warning_symptoms),
    }
