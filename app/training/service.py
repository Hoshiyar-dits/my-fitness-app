from datetime import date, timedelta
from typing import List, Optional
from fastapi import Depends, HTTPException
from pydantic import ValidationError
from app.activities.metrics import same_distance
from app.activities.models.performance_activity import PerformanceActivity
from app.activities.service import ActivityService
from app.body_metrics.repository import BodyMetricRepository
from app.database.types import utcnow
from app.goals.dto.CreateGoal import CreateGoal
from app.goals.models.fitness_goal import FitnessGoal
from app.training import program_generator as generator
from app.training.models.training import TrainingProgram, PlannedWorkout, PlannedExercise, PerformedExercise
from app.training.program_generator import SessionSpec, ExerciseSpec, ProgramSettings
from app.training.repository import ExerciseRepository, ProgramRepository, PlanRepository
from app.users.repository import UserRepository
from app.workouts.models.workout import Workout

WORKOUT_TYPE_FOR_SESSION = {
    "sprint": "sports",
    "endurance_run": "cardio",
    "long_jump": "sports",
    "high_jump": "sports",
    "strength": "strength",
    "mobility": "flexibility",
    "recovery": "flexibility",
    "assessment": "sports",
}
CLEARANCE_MESSAGE = (
    "You reported current pain or a medical restriction. Please get clearance from a doctor or physiotherapist "
    "before starting strenuous sprint and jump training. Your 25-day calendar will be created once you confirm "
    "clearance (PATCH /programs/{id} with medical_clearance_confirmed=true)."
)
MINOR_MESSAGE = "As you are under 18, please train under the supervision of a qualified coach or responsible adult."


def plan_from_spec(exercises: ExerciseRepository, user_id: int, program_id: Optional[int], plan_date: date, spec: SessionSpec,
                   source: str, status: str, adjustment_reason: Optional[str] = None, based_on_plan_id: Optional[int] = None) -> PlannedWorkout:
    plan = PlannedWorkout(
        user_id=user_id, program_id=program_id, plan_date=plan_date, day_number=spec.day_number, training_phase=spec.phase,
        session_type=spec.session_type, title=spec.title, description=spec.description, warm_up=spec.warm_up,
        cool_down=spec.cool_down, intensity=spec.intensity, estimated_duration_minutes=spec.minutes,
        is_high_impact=spec.is_high_impact, source=source, status=status,
        confirmed_at=utcnow() if status == "confirmed" else None,
        adjustment_reason=adjustment_reason, based_on_plan_id=based_on_plan_id, completion_status="pending",
    )
    plan.exercises = [
        PlannedExercise(
            exercise_id=exercises.get_by_name(e.name).id, position=position, sets=e.sets, reps=e.reps,
            distance_m=e.distance_m, duration_seconds=e.duration_seconds, rest_seconds=e.rest_seconds,
            effort=e.effort, notes=e.notes,
        )
        for position, e in enumerate(spec.exercises, start=1)
    ]
    return plan


def spec_from_plan(plan: PlannedWorkout) -> SessionSpec:
    return SessionSpec(
        session_type=plan.session_type, title=plan.title, intensity=plan.intensity, minutes=plan.estimated_duration_minutes,
        description=plan.description or "", day_number=plan.day_number, phase=plan.training_phase,
        warm_up=plan.warm_up, cool_down=plan.cool_down,
        exercises=[
            ExerciseSpec(e.exercise.name, sets=e.sets, reps=e.reps, distance_m=float(e.distance_m) if e.distance_m is not None else None,
                         duration_seconds=e.duration_seconds, rest_seconds=e.rest_seconds, effort=e.effort, notes=e.notes)
            for e in plan.exercises
        ],
    )


def _age(date_of_birth: date, today: date) -> int:
    return today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))


class ProgramService():
    def __init__(
        self,
        programs: ProgramRepository = Depends(),
        plans: PlanRepository = Depends(),
        exercises: ExerciseRepository = Depends(),
        users: UserRepository = Depends(),
        body_metrics: BodyMetricRepository = Depends(),
    ):
        self.programs = programs
        self.plans = plans
        self.exercises = exercises
        self.users = users
        self.body_metrics = body_metrics

    def current(self, user_id: int):
        program = self.programs.current(user_id)
        if not program:
            raise HTTPException(status_code=404, detail="No training program yet")
        if program.status == "active" and program.end_date < date.today():
            program = self.programs.update(program, {"status": "completed"})
        return program

    def get(self, user_id: int, program_id: int):
        program = self.programs.get(user_id, program_id)
        if not program:
            raise HTTPException(status_code=404, detail="Program not found")
        return program

    def create(self, user_id: int, data):
        if self.programs.open_program(user_id):
            raise HTTPException(status_code=409, detail="You already have an open program. Cancel it before starting a new one.")

        today = date.today()
        needs_clearance = bool(data.current_pain or data.medical_restrictions) and not data.medical_clearance_confirmed
        level = data.experience_level
        program = TrainingProgram(
            user_id=user_id, start_date=data.start_date, end_date=data.start_date + timedelta(days=generator.PROGRAM_DAYS - 1),
            status="awaiting_clearance" if needs_clearance else "active", experience_level=level,
            training_background=data.training_background, available_minutes_per_day=data.available_minutes_per_day,
            equipment=list(data.equipment), injury_history=data.injury_history, current_pain=data.current_pain,
            medical_restrictions=data.medical_restrictions, medical_clearance_confirmed=data.medical_clearance_confirmed,
            assessment_run_distance_m=data.assessment_run_distance_m or generator.default_run_assessment_m(level),
            assessment_sprint_distance_m=data.assessment_sprint_distance_m or generator.DEFAULT_SPRINT_ASSESSMENT_M,
            notes=data.notes,
        )
        self.programs.save_all([program])

        try:
            sessions = [] if needs_clearance else self._calendar(program)
            goals = self._goals(user_id, program, data)
            baseline = self._baseline_activities(user_id, program, data.baseline, today)
            self.programs.save_all(sessions + goals + baseline)
        except Exception:
            # keep onboarding all-or-nothing: without its sessions the program is useless
            self.programs.delete(program)
            raise

        if data.baseline and data.baseline.weight_kg is not None:
            self.body_metrics.upsert(user_id, {
                "log_date": today, "weight_kg": data.baseline.weight_kg,
                "body_fat_pct": data.baseline.body_fat_pct, "body_fat_method": data.baseline.body_fat_method,
            })

        safety = [CLEARANCE_MESSAGE.replace("{id}", str(program.id))] if needs_clearance else []
        profile = self.users.get_profile(user_id)
        if profile and _age(profile.date_of_birth, today) < 18:
            safety.append(MINOR_MESSAGE)
        return {
            "program": program,
            "sessions_created": len(sessions),
            "goals_created": len(goals),
            "safety_message": " ".join(safety) or None,
            "missing_information": self._missing_information(profile, data),
        }

    def update(self, user_id: int, program_id: int, data):
        program = self.get(user_id, program_id)
        changes = data.model_dump(exclude_unset=True)
        if changes.get("status") == "cancelled":
            if program.status not in ("active", "awaiting_clearance"):
                raise HTTPException(status_code=409, detail=f"Program is already {program.status}")
            upcoming = [p for p in self.plans.for_program(program.id)
                        if p.plan_date >= date.today() and p.completion_status == "pending" and p.status in ("proposed", "confirmed")]
            self.plans.update_many(upcoming, {"status": "cancelled"})
            return self.programs.update(program, {"status": "cancelled"})
        if changes.get("medical_clearance_confirmed"):
            if program.status != "awaiting_clearance":
                raise HTTPException(status_code=409, detail="Program is not waiting for medical clearance")
            start = max(program.start_date, date.today())
            program = self.programs.update(program, {
                "medical_clearance_confirmed": True, "status": "active", "start_date": start,
                "end_date": start + timedelta(days=generator.PROGRAM_DAYS - 1),
            })
            self.programs.save_all(self._calendar(program))
            return program
        raise HTTPException(status_code=422, detail="Nothing to update")

    def _settings(self, program: TrainingProgram) -> ProgramSettings:
        return ProgramSettings(
            level=program.experience_level, available_minutes=program.available_minutes_per_day,
            equipment=list(program.equipment or []), run_assessment_m=float(program.assessment_run_distance_m),
            sprint_assessment_m=float(program.assessment_sprint_distance_m),
        )

    def _calendar(self, program: TrainingProgram) -> List[PlannedWorkout]:
        return [
            plan_from_spec(self.exercises, program.user_id, program.id, program.start_date + timedelta(days=spec.day_number - 1),
                           spec, source="program_template", status="confirmed")
            for spec in generator.build_calendar(self._settings(program))
        ]

    def _goals(self, user_id: int, program: TrainingProgram, data) -> List[FitnessGoal]:
        targets, baseline = data.targets, data.baseline
        if not targets:
            return []
        run_m, sprint_m = program.assessment_run_distance_m, program.assessment_sprint_distance_m
        candidates = []
        if targets.run_elapsed_seconds is not None:
            # a self-reported time only counts as baseline if it was over the assessment distance
            comparable = baseline and baseline.run_distance_m and same_distance(baseline.run_distance_m, run_m)
            candidates.append(dict(goal_type="running_time", reference_distance_m=run_m, target_value=targets.run_elapsed_seconds,
                                   baseline_value=baseline.run_elapsed_seconds if comparable else None))
        if targets.sprint_elapsed_seconds is not None:
            comparable = baseline and baseline.sprint_distance_m and same_distance(baseline.sprint_distance_m, sprint_m)
            candidates.append(dict(goal_type="sprint_time", reference_distance_m=sprint_m, target_value=targets.sprint_elapsed_seconds,
                                   baseline_value=baseline.sprint_elapsed_seconds if comparable else None))
        if targets.long_jump_cm is not None:
            comparable = baseline and baseline.long_jump_cm and baseline.long_jump_technique == "standing"
            candidates.append(dict(goal_type="long_jump", technique="standing", target_value=targets.long_jump_cm,
                                   baseline_value=baseline.long_jump_cm if comparable else None))
        if targets.high_jump_cm is not None:
            candidates.append(dict(goal_type="high_jump", target_value=targets.high_jump_cm,
                                   baseline_value=baseline.high_jump_cm if baseline else None))
        if targets.weight_kg is not None:
            candidates.append(dict(goal_type="body_weight", target_value=targets.weight_kg,
                                   baseline_value=baseline.weight_kg if baseline else None))
        if targets.body_fat_pct is not None:
            candidates.append(dict(goal_type="body_fat", target_value=targets.body_fat_pct,
                                   baseline_value=baseline.body_fat_pct if baseline else None))

        goals = []
        for values in candidates:
            try:
                goal = CreateGoal(start_date=program.start_date, target_date=program.end_date, program_id=program.id, **values)
            except ValidationError as e:
                raise HTTPException(status_code=422, detail=f"targets.{values['goal_type']}: {e.errors()[0]['msg']}")
            goals.append(FitnessGoal(user_id=user_id, status="active", **goal.model_dump()))
        return goals

    def _baseline_activities(self, user_id: int, program: TrainingProgram, baseline, today: date) -> List[PerformanceActivity]:
        if not baseline:
            return []
        common = dict(user_id=user_id, activity_date=today, measurement_method="self_reported", is_assessment=False,
                      notes="Self-reported at onboarding")
        rows = []
        if baseline.run_distance_m:
            rows.append(PerformanceActivity(activity_type="run", distance_m=baseline.run_distance_m,
                                            elapsed_seconds=baseline.run_elapsed_seconds, **common))
        if baseline.sprint_distance_m:
            rows.append(PerformanceActivity(activity_type="sprint", distance_m=baseline.sprint_distance_m,
                                            elapsed_seconds=baseline.sprint_elapsed_seconds, **common))
        if baseline.long_jump_cm:
            rows.append(PerformanceActivity(activity_type="long_jump", jump_cm=baseline.long_jump_cm,
                                            technique=baseline.long_jump_technique, **common))
        if baseline.high_jump_cm:
            rows.append(PerformanceActivity(activity_type="high_jump", jump_cm=baseline.high_jump_cm,
                                            technique=baseline.high_jump_technique, **common))
        return rows

    def _missing_information(self, profile, data) -> List[str]:
        missing = []
        if not profile:
            missing.append("Add your date of birth and height to your profile (POST /user/profile) so advice can account for age.")
        baseline = data.baseline
        if not baseline or not baseline.run_distance_m:
            missing.append("No current running time given. The day-3 running assessment will set your baseline.")
        if not baseline or not baseline.long_jump_cm:
            missing.append("No current long jump given. The day-1 assessment will set your baseline.")
        if not baseline or not baseline.weight_kg:
            missing.append("No current body weight given. Log weigh-ins (same time of day, same scale) to track the trend.")
        if "high_jump_setup" not in data.equipment:
            missing.append("No high jump bar and landing mat listed, so high jump sessions use bar-free drills and no height is measured.")
        return missing


class PlanService():
    def __init__(
        self,
        plans: PlanRepository = Depends(),
        exercises: ExerciseRepository = Depends(),
        activities: ActivityService = Depends(),
    ):
        self.plans = plans
        self.exercises = exercises
        self.activities = activities

    def get(self, user_id: int, plan_id: int):
        plan = self.plans.get(user_id, plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        return plan

    def today(self, user_id: int):
        today = date.today()
        return self.plans.list(user_id, today, today, ["confirmed", "proposed"])

    def list(self, user_id: int, from_date, to_date, status: Optional[str], limit: int, offset: int):
        if from_date and to_date and to_date < from_date:
            raise HTTPException(status_code=422, detail="to_date must be on or after from_date")
        return self.plans.list(user_id, from_date, to_date, [status] if status else None, limit, offset)

    def create(self, user_id: int, data):
        known = self.exercises.get_many(e.exercise_id for e in data.exercises)
        unknown = sorted({e.exercise_id for e in data.exercises} - set(known))
        if unknown:
            raise HTTPException(status_code=422, detail=f"Unknown exercise ids: {unknown}")
        plan = PlannedWorkout(
            user_id=user_id, plan_date=data.plan_date, session_type=data.session_type, title=data.title,
            description=data.description, intensity=data.intensity, estimated_duration_minutes=data.estimated_duration_minutes,
            is_high_impact=any(known[e.exercise_id].is_high_impact for e in data.exercises),
            source="user", status="confirmed", confirmed_at=utcnow(), completion_status="pending",
        )
        plan.exercises = [PlannedExercise(position=i, **e.model_dump()) for i, e in enumerate(data.exercises, start=1)]
        return self.plans.add(plan)

    def update(self, user_id: int, plan_id: int, data):
        plan = self.get(user_id, plan_id)
        changes = data.model_dump(exclude_unset=True)
        new_status = changes.pop("status", None)
        for field in ("plan_date", "title", "intensity", "estimated_duration_minutes"):
            if field in changes and changes[field] is None:
                raise HTTPException(status_code=422, detail=f"{field} cannot be null")
        if changes:
            if plan.completion_status != "pending" or plan.status not in ("proposed", "confirmed"):
                raise HTTPException(status_code=409, detail="Only pending, live plans can be edited")
            if "plan_date" in changes and changes["plan_date"] < date.today():
                raise HTTPException(status_code=422, detail="plan_date cannot be moved into the past")
        if new_status == "confirmed":
            return self.confirm(plan, changes)
        if new_status == "rejected":
            if plan.status != "proposed":
                raise HTTPException(status_code=409, detail="Only proposed plans can be rejected")
            changes["status"] = "rejected"
        return self.plans.update(plan, changes)

    def confirm(self, plan: PlannedWorkout, changes: Optional[dict] = None):
        """Accepts a proposed plan. The plan it was adjusted from (and competing proposals for it) are superseded."""
        if plan.status != "proposed":
            raise HTTPException(status_code=409, detail=f"Only proposed plans can be confirmed (this one is {plan.status})")
        if plan.plan_date < date.today():
            raise HTTPException(status_code=409, detail="This proposal is for a past date")
        replaced = []
        if plan.based_on_plan_id:
            original = self.plans.get(plan.user_id, plan.based_on_plan_id)
            if original and original.status == "confirmed" and original.completion_status == "pending":
                replaced.append(original)
            replaced += [p for p in self.plans.list(plan.user_id, plan.plan_date, plan.plan_date, ["proposed"])
                         if p.id != plan.id and p.based_on_plan_id == plan.based_on_plan_id]
        self.plans.update_many(replaced, {"status": "superseded"})
        return self.plans.update(plan, {**(changes or {}), "status": "confirmed", "confirmed_at": utcnow()})

    def complete(self, user_id: int, plan_id: int, data):
        plan = self.get(user_id, plan_id)
        if plan.status != "confirmed":
            raise HTTPException(status_code=409, detail="Only confirmed plans can be completed. Confirm the proposal first.")
        if plan.completion_status != "pending":
            raise HTTPException(status_code=409, detail=f"Plan is already {plan.completion_status}")
        if plan.session_type == "rest":
            raise HTTPException(status_code=422, detail="Rest days have nothing to complete")
        if plan.plan_date > date.today():
            raise HTTPException(status_code=422, detail="Plans for future dates cannot be completed yet")
        known = self.exercises.get_many(e.exercise_id for e in data.performed_exercises)
        unknown = sorted({e.exercise_id for e in data.performed_exercises} - set(known))
        if unknown:
            raise HTTPException(status_code=422, detail=f"Unknown exercise ids: {unknown}")

        # also logged as a regular workout so the existing dashboard, streak and calorie totals include it
        workout = Workout(
            user_id=user_id, workout_date=plan.plan_date, workout_type=WORKOUT_TYPE_FOR_SESSION.get(plan.session_type, "other"),
            name=plan.title[:255], duration_minutes=data.actual_duration_minutes, calories_burned=data.calories_burned,
            intensity=plan.intensity, notes=data.notes,
        )
        performed = [PerformedExercise(planned_workout_id=plan.id, **e.model_dump()) for e in data.performed_exercises]
        plan = self.plans.complete(plan, {
            "completion_status": data.completion_status, "actual_duration_minutes": data.actual_duration_minutes,
            "perceived_effort": data.perceived_effort, "completion_notes": data.notes, "completed_at": utcnow(),
        }, workout, performed)
        for activity in data.activities:
            self.activities.create(user_id, activity, planned_workout_id=plan.id)
        return self.get(user_id, plan.id)

    def skip(self, user_id: int, plan_id: int, reason: str):
        plan = self.get(user_id, plan_id)
        if plan.status != "confirmed":
            raise HTTPException(status_code=409, detail="Only confirmed plans can be skipped")
        if plan.completion_status != "pending":
            raise HTTPException(status_code=409, detail=f"Plan is already {plan.completion_status}")
        return self.plans.update(plan, {"completion_status": "skipped", "skip_reason": reason})
