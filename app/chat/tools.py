"""Tools the AI coach can call, exposed to LangChain as StructuredTools. Each tool runs through the normal
services for the authenticated user only: the user id is bound server-side (bind()) and is never a tool
argument, arguments are validated with Pydantic, and there is no free-form query access. Errors are returned
to the model as {"ok": false}, never as fabricated results."""
import json
import logging
from datetime import date, timedelta
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple, Type, Union
from fastapi import Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field, ValidationError
from app.activities.metrics import measurement_trend, pace_seconds_per_km, performance_comparison
from app.activities.repository import ActivityRepository
from app.analysis.service import AnalysisService
from app.body_metrics.repository import BodyMetricRepository
from app.checkins.dto.CheckinResponse import CheckinResponse
from app.checkins.service import CheckinService
from app.goals.dto.GoalResponse import GoalResponse
from app.goals.service import GoalService
from app.progress.service import ProgressService
from app.progress.training_service import TrainingProgressService
from app.training.repository import PlanRepository
from app.training.service import PlanService
from app.workouts.repository import WorkoutRepository

logger = logging.getLogger(__name__)
MAX_LOOKBACK_DAYS = 90


class NoArgs(BaseModel):
    pass

class DaysArgs(BaseModel):
    days: int = Field(default=14, ge=1, le=MAX_LOOKBACK_DAYS, description="How many days back to look, including today")

class DaysAheadArgs(BaseModel):
    days: int = Field(default=7, ge=1, le=30, description="How many days ahead to look, including today")

class GoalArgs(BaseModel):
    status: Optional[Literal["active", "achieved", "abandoned", "expired"]] = Field(default="active", description="Omit or null for all")

class DateArgs(BaseModel):
    day: Optional[date] = Field(default=None, description="YYYY-MM-DD, defaults to today")

class WeekArgs(BaseModel):
    week_of: Optional[date] = Field(default=None, description="Any date in the Monday-Sunday week, defaults to this week")

class SaveArgs(BaseModel):
    plan_id: int = Field(description="id of a proposed plan returned by propose_tomorrow_workout")
    user_confirmed: bool = Field(description="True only if the user explicitly agreed to this specific proposed plan")


def _plan_brief(plan) -> dict:
    return {
        "plan_id": plan.id, "date": plan.plan_date, "day_number": plan.day_number, "phase": plan.training_phase,
        "title": plan.title, "session_type": plan.session_type, "intensity": plan.intensity,
        "estimated_minutes": plan.estimated_duration_minutes, "high_impact": plan.is_high_impact,
        "status": plan.status, "source": plan.source, "completion_status": plan.completion_status,
        "actual_minutes": plan.actual_duration_minutes, "perceived_effort": plan.perceived_effort,
        "skip_reason": plan.skip_reason, "adjustment_reason": plan.adjustment_reason,
        "exercises": [
            {k: v for k, v in {
                "name": e.exercise_name, "sets": e.sets, "reps": e.reps, "distance_m": e.distance_m,
                "duration_seconds": e.duration_seconds, "rest_seconds": e.rest_seconds, "effort": e.effort,
            }.items() if v is not None}
            for e in plan.exercises
        ],
    }


def _activity_brief(a) -> dict:
    row = {"id": a.id, "date": a.activity_date, "type": a.activity_type, "assessment": a.is_assessment,
           "method": a.measurement_method, "effort": a.perceived_effort}
    if a.activity_type in ("run", "sprint"):
        row.update(distance_m=a.distance_m, elapsed_seconds=a.elapsed_seconds,
                   pace_seconds_per_km=pace_seconds_per_km(a.distance_m, a.elapsed_seconds))
    else:
        row.update(jump_cm=a.jump_cm, technique=a.technique, attempt=a.attempt_number)
    return row


class FitnessToolbox():
    def __init__(
        self,
        goals: GoalService = Depends(),
        plans: PlanService = Depends(),
        plan_repository: PlanRepository = Depends(),
        checkins: CheckinService = Depends(),
        activities: ActivityRepository = Depends(),
        body_metrics: BodyMetricRepository = Depends(),
        workouts: WorkoutRepository = Depends(),
        progress: ProgressService = Depends(),
        training_progress: TrainingProgressService = Depends(),
        analysis: AnalysisService = Depends(),
    ):
        self.goals = goals
        self.plans = plans
        self.plan_repository = plan_repository
        self.checkins = checkins
        self.activities = activities
        self.body_metrics = body_metrics
        self.workouts = workouts
        self.progress = progress
        self.training_progress = training_progress
        self.analysis = analysis
        self.user_id: Optional[int] = None
        self.actions: List[dict] = []
        self._proposed_this_turn: set = set()
        self._tools: Dict[str, Tuple[str, Type[BaseModel], Callable]] = {
            "get_user_goals": ("The user's fitness goals with baseline, target and current values (explicit units).", GoalArgs, self._goals),
            "get_workout_history": ("Planned sessions in the last N days with completion status, effort and skip reasons, plus other logged workouts.", DaysArgs, self._workout_history),
            "get_upcoming_plans": ("Confirmed and proposed sessions from today for the next N days, with exercises.", DaysAheadArgs, self._upcoming),
            "get_daily_checkin": ("The user's check-in (sleep, energy, fatigue, soreness, pain, warning symptoms) for a date.", DateArgs, self._checkin),
            "get_running_progress": ("Recent runs and sprints with pace, and baseline-vs-latest comparisons over the same distance.", DaysArgs, self._running),
            "get_jump_performance": ("Recent long and high jump measurements and baseline-vs-latest comparisons with the same technique.", DaysArgs, self._jumps),
            "get_body_measurement_history": ("Weigh-ins and body-fat estimates, with multi-day trends.", DaysArgs, self._body),
            "get_nutrition_summary": ("Logged food totals for the last N days (calories, protein, carbs, fat). Logging food is optional.", DaysArgs, self._nutrition),
            "get_weekly_progress": ("Weekly totals: sessions planned/completed/skipped, effort, check-in averages, performance changes.", WeekArgs, self._weekly),
            "get_program_progress": ("Progress over the current 25-day program: adherence, assessments vs baseline, weight trend, goals.", NoArgs, self._program),
            "propose_tomorrow_workout": ("Review today's data with the safety rules and propose tomorrow's workout. Saves an unconfirmed proposal if a change is needed.", NoArgs, self._propose),
            "save_confirmed_workout_plan": ("Confirm a proposed plan. Only after the user explicitly agreed to it in their latest message.", SaveArgs, self._save),
        }

    def bind(self, user_id: int):
        self.user_id = user_id
        self.actions = []
        self._proposed_this_turn = set()

    def langchain_tools(self) -> List[StructuredTool]:
        """LangChain tools for bind_tools(). Arguments are validated in call(), so a bad argument becomes an
        {"ok": false} result for the model instead of an exception."""
        return [
            StructuredTool.from_function(
                func=lambda _name=name, **arguments: json.dumps(self.call(_name, arguments), default=str),
                name=name, description=description, args_schema=args_model, infer_schema=False,
                handle_validation_error=lambda e: json.dumps({"ok": False, "error": f"Invalid arguments: {e}"}),
            )
            for name, (description, args_model, _) in self._tools.items()
        ]

    def call(self, name: str, arguments: Union[str, Dict[str, Any], None]) -> dict:
        if self.user_id is None:
            raise RuntimeError("FitnessToolbox.bind() must be called before tools are used")
        if name not in self._tools:
            return {"ok": False, "error": f"Unknown tool '{name}'"}
        _, args_model, handler = self._tools[name]
        try:
            if isinstance(arguments, str) or arguments is None:
                args = args_model.model_validate_json(arguments or "{}")
            else:
                args = args_model.model_validate(arguments)
        except ValidationError as e:
            return {"ok": False, "error": f"Invalid arguments: {e.errors(include_url=False)}"}
        try:
            data = handler(args)
        except HTTPException as e:
            self.actions.append({"tool": name, "ok": False})
            return {"ok": False, "error": e.detail}
        except Exception:
            logger.exception("Tool %s failed", name)
            self.actions.append({"tool": name, "ok": False})
            return {"ok": False, "error": "The tool failed. Tell the user the data could not be loaded right now."}
        self.actions.append({"tool": name, "ok": True, "plan_ids": data.get("plan_ids", []) if isinstance(data, dict) else []})
        return {"ok": True, "data": jsonable_encoder(data)}

    # --- read tools -----------------------------------------------------------------

    def _since(self, days: int) -> date:
        return date.today() - timedelta(days=days - 1)

    def _goals(self, args: GoalArgs):
        goals = self.goals.list(self.user_id, args.status, 50, 0)
        return {"goals": [GoalResponse.model_validate(g).model_dump(exclude={"created_at", "updated_at"}) for g in goals]}

    def _workout_history(self, args: DaysArgs):
        start, today = self._since(args.days), date.today()
        plans = self.plan_repository.list(self.user_id, start, today, ["confirmed"])
        linked = {p.workout_id for p in plans if p.workout_id}
        other = [w for w in self.workouts.list(self.user_id, start, today, limit=50, offset=0) if w.id not in linked]
        return {
            "from": start, "to": today,
            "planned_sessions": [{k: v for k, v in _plan_brief(p).items() if k != "exercises"} for p in plans],
            "other_logged_workouts": [{"date": w.workout_date, "type": w.workout_type, "name": w.name,
                                       "minutes": w.duration_minutes, "intensity": w.intensity} for w in other],
        }

    def _upcoming(self, args: DaysAheadArgs):
        today = date.today()
        plans = self.plan_repository.list(self.user_id, today, today + timedelta(days=args.days - 1), ["confirmed", "proposed"])
        return {"plans": [_plan_brief(p) for p in plans]}

    def _checkin(self, args: DateArgs):
        day = args.day or date.today()
        if day > date.today() or day < date.today() - timedelta(days=MAX_LOOKBACK_DAYS):
            raise HTTPException(status_code=422, detail=f"day must be within the last {MAX_LOOKBACK_DAYS} days")
        checkin = self.checkins.by_date(self.user_id, day)
        if not checkin:
            return {"date": day, "checkin": None, "note": "No check-in recorded for this date."}
        return {"date": day, "checkin": CheckinResponse.model_validate(checkin).model_dump(exclude={"created_at", "updated_at"})}

    def _comparisons(self, activities, kinds):
        results = []
        for kind in kinds:
            latest = next((a for a in activities if a.activity_type == kind), None)  # newest first
            if latest is None:
                continue
            if kind in ("run", "sprint"):
                results.append(performance_comparison(activities, kind, reference_distance_m=latest.distance_m))
            else:
                results.append(performance_comparison(activities, kind, technique=latest.technique))
        return results

    def _running(self, args: DaysArgs):
        activities = self.activities.list(self.user_id, ["run", "sprint"], self._since(args.days), date.today(), limit=200)
        return {"recent": [_activity_brief(a) for a in activities[:25]],
                "comparisons": self._comparisons(activities, ("run", "sprint")),
                "units": "distance m, time s, pace s/km"}

    def _jumps(self, args: DaysArgs):
        activities = self.activities.list(self.user_id, ["long_jump", "high_jump"], self._since(args.days), date.today(), limit=200)
        return {"recent": [_activity_brief(a) for a in activities[:25]],
                "comparisons": self._comparisons(activities, ("long_jump", "high_jump")),
                "units": "cm"}

    def _body(self, args: DaysArgs):
        metrics = self.body_metrics.list(self.user_id, self._since(args.days), date.today(), 366)
        fat = [m for m in metrics if m.body_fat_pct is not None]
        method = fat[0].body_fat_method if fat else None
        return {
            "readings": [{"date": m.log_date, "weight_kg": m.weight_kg, "body_fat_pct": m.body_fat_pct,
                          "body_fat_method": m.body_fat_method} for m in metrics[:30]],
            "weight_trend": measurement_trend([(m.log_date, m.weight_kg) for m in metrics], "body_weight"),
            "body_fat_trend": {**measurement_trend([(m.log_date, m.body_fat_pct) for m in fat if m.body_fat_method == method], "body_fat"),
                               "method": method},
        }

    def _nutrition(self, args: DaysArgs):
        summary = self.progress.period(self.user_id, self._since(min(args.days, 31)), date.today())
        return {
            "totals": summary.totals.model_dump(),
            "days": [{"date": d.date, "calories": d.calories_consumed, "verified_calories": d.calories_verified,
                      "protein_g": d.protein_g, "meals": d.meals_count} for d in summary.days],
            "note": "Calories not marked verified are the user's estimates. Days without meals were simply not logged.",
        }

    def _weekly(self, args: WeekArgs):
        return self.training_progress.weekly(self.user_id, args.week_of or date.today()).model_dump(exclude={"days"})

    def _program(self, args: NoArgs):
        return self.training_progress.program_report(self.user_id).model_dump()

    # --- write tools ------------------------------------------------------------------

    def _propose(self, args: NoArgs):
        result = self.analysis.propose_tomorrow(self.user_id, date.today(), source="ai_agent")
        proposed_ids = [p.id for p in result["proposed_plans"]]
        self._proposed_this_turn.update(proposed_ids)
        return {
            "date": result["date"], "decision": result["decision"], "reasons": result["reasons"],
            "safety_message": result["safety_message"], "message": result["message"],
            "requires_confirmation": result["requires_confirmation"],
            "scheduled": [_plan_brief(p) for p in result["scheduled_plans"]],
            "proposed": [_plan_brief(p) for p in result["proposed_plans"]],
            "plan_ids": proposed_ids,
        }

    def _save(self, args: SaveArgs):
        if not args.user_confirmed:
            raise HTTPException(status_code=409, detail="Ask the user to confirm the proposed plan before saving it.")
        if args.plan_id in self._proposed_this_turn:
            # the user cannot have agreed to a plan they have not been shown yet
            raise HTTPException(status_code=409, detail="This plan was only just proposed. Show it to the user and wait for them to confirm it.")
        plan = self.plans.get(self.user_id, args.plan_id)
        plan = self.plans.confirm(plan)
        return {"saved": True, "plan": _plan_brief(plan), "plan_ids": [plan.id]}
