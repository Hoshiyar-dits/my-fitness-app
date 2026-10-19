from datetime import date, timedelta
from typing import List
from fastapi import Depends
from fastapi.encoders import jsonable_encoder
from app.activities.metrics import performance_comparison, pace_seconds_per_km
from app.activities.repository import ActivityRepository
from app.analysis.readiness import Readiness, adjust_session, assess_readiness
from app.analysis.repository import AnalysisRepository
from app.checkins.repository import CheckinRepository
from app.training.repository import ExerciseRepository, PlanRepository, ProgramRepository
from app.training.service import plan_from_spec, spec_from_plan

COMPARISON_WINDOW_DAYS = 60
RECOMMENDATIONS = {
    "proceed": "Train as planned tomorrow.",
    "proceed_with_caution": "Tomorrow's plan stays the same, but complete a check-in first so it can be adjusted if needed.",
    "modify": "Do a lighter version of tomorrow's session.",
    "recovery": "Swap tomorrow's session for active recovery.",
    "stop": "Do not train. Get a medical assessment before training again.",
}


class AnalysisService():
    def __init__(
        self,
        analyses: AnalysisRepository = Depends(),
        checkins: CheckinRepository = Depends(),
        plans: PlanRepository = Depends(),
        programs: ProgramRepository = Depends(),
        exercises: ExerciseRepository = Depends(),
        activities: ActivityRepository = Depends(),
    ):
        self.analyses = analyses
        self.checkins = checkins
        self.plans = plans
        self.programs = programs
        self.exercises = exercises
        self.activities = activities

    def daily(self, user_id: int, day: date):
        analysis, _, _ = self._analyse(user_id, day)
        return analysis

    def propose_tomorrow(self, user_id: int, today: date, source: str):
        """Proposes changes to tomorrow's confirmed sessions based on today's data. Proposals are never
        confirmed here. Calling this again replaces earlier proposals for the same sessions."""
        analysis, readiness, high_impact_today = self._analyse(user_id, today)
        tomorrow = today + timedelta(days=1)
        scheduled = [p for p in self.plans.confirmed_on(user_id, tomorrow) if p.completion_status == "pending"]
        open_proposals = self.plans.list(user_id, tomorrow, tomorrow, ["proposed"])

        proposals = []
        for plan in scheduled:
            # earlier proposals for this session are outdated now, whether or not a new change is needed
            self.plans.update_many([p for p in open_proposals if p.based_on_plan_id == plan.id], {"status": "superseded"})
            adjusted = adjust_session(spec_from_plan(plan), readiness, high_impact_today)
            if not adjusted:
                continue
            spec, why = adjusted
            proposals.append(self.plans.add(plan_from_spec(
                self.exercises, user_id, plan.program_id, tomorrow, spec, source=source, status="proposed",
                adjustment_reason=" ".join(why), based_on_plan_id=plan.id,
            )))

        analysis = self.analyses.upsert(user_id, today, {"proposed_plan_id": proposals[0].id if proposals else None})
        if proposals:
            message = "A changed plan for tomorrow has been proposed. It only replaces your plan once you confirm it."
        elif scheduled:
            message = "Tomorrow's session can go ahead as planned."
        else:
            message = "Nothing is scheduled for tomorrow."

        reasons = list(readiness.reasons) + [p.adjustment_reason for p in proposals]
        return {
            "date": tomorrow,
            "decision": readiness.decision,
            "reasons": reasons,
            "safety_message": readiness.safety_message,
            "message": message,
            "requires_confirmation": bool(proposals),
            "scheduled_plans": scheduled,
            "proposed_plans": proposals,
            "analysis": analysis,
        }

    def _analyse(self, user_id: int, day: date):
        checkin = self.checkins.get_by_date(user_id, day)
        recent_checkins = self.checkins.list(user_id, day - timedelta(days=3), day - timedelta(days=1))
        plans = self.plans.confirmed_on(user_id, day)
        activities = self.activities.list(user_id, None, day, day)
        program = self.programs.current(user_id)
        readiness = assess_readiness(checkin, recent_checkins)

        training = [p for p in plans if p.session_type != "rest"]
        done = [p for p in training if p.completion_status in ("completed", "partial")]
        skipped = [p for p in training if p.completion_status == "skipped"]
        not_logged = [p for p in training if p.completion_status == "pending"]
        high_impact_today = any(p.is_high_impact for p in done) or any(
            a.activity_type in ("sprint", "long_jump", "high_jump") for a in activities)

        reasons = list(readiness.reasons)
        if skipped or (not_logged and day < date.today()):
            reasons.append("A planned session was not completed. Tomorrow's workload is not increased to make up for it.")
        efforts = [p.perceived_effort for p in done if p.perceived_effort is not None]
        if efforts and max(efforts) >= 9:
            reasons.append("Today's session felt very hard (effort 9-10/10).")

        performance = self._performance(user_id, day, activities)
        summary = self._summary(training, done, skipped, not_logged, checkin, performance, readiness)
        metrics = {
            "planned_sessions": len(training),
            "completed_sessions": len(done),
            "skipped_sessions": len(skipped),
            "not_logged_sessions": len(not_logged),
            "actual_minutes": sum(p.actual_duration_minutes or 0 for p in done),
            "planned_minutes": sum(p.estimated_duration_minutes for p in training),
            "max_perceived_effort": max(efforts) if efforts else None,
            "high_impact_today": high_impact_today,
            "skip_reasons": [p.skip_reason for p in skipped],
            "performance": performance,
        }
        analysis = self.analyses.upsert(user_id, day, {
            "program_id": program.id if program else None,
            "readiness": readiness.decision,
            "summary": summary,
            "reasons": reasons,
            "metrics": jsonable_encoder(metrics),
            "source_refs": {
                "checkin_id": checkin.id if checkin else None,
                "previous_checkin_ids": [c.id for c in recent_checkins],
                "plan_ids": [p.id for p in plans],
                "activity_ids": [a.id for a in activities],
            },
            "recommendation": RECOMMENDATIONS[readiness.decision],
            "safety_message": readiness.safety_message,
            "generated_by": "rules",
        })
        return analysis, readiness, high_impact_today

    def _performance(self, user_id: int, day: date, today_activities) -> List[dict]:
        results = []
        for kind in ("run", "sprint", "long_jump", "high_jump"):
            todays = [a for a in today_activities if a.activity_type == kind]
            if not todays:
                continue
            history = self.activities.list(user_id, [kind], day - timedelta(days=COMPARISON_WINDOW_DAYS), day)
            # compare against today's measurement type: same distance for runs, same technique for jumps
            reference = todays[0]
            if kind in ("run", "sprint"):
                results.append(performance_comparison(history, kind, reference_distance_m=reference.distance_m))
            else:
                results.append(performance_comparison(history, kind, technique=reference.technique))
        return results

    def _summary(self, training, done, skipped, not_logged, checkin, performance, readiness: Readiness) -> str:
        lines = []
        if not training:
            lines.append("No training was planned (rest day or no plan).")
        else:
            lines.append(f"{len(done)} of {len(training)} planned sessions completed"
                         + (f", {len(skipped)} skipped" if skipped else "")
                         + (f", {len(not_logged)} not logged yet" if not_logged else "") + ".")
        if checkin:
            parts = []
            if checkin.sleep_hours is not None:
                parts.append(f"sleep {checkin.sleep_hours} h")
            for label, value in (("energy", checkin.energy_level), ("fatigue", checkin.fatigue_level), ("soreness", checkin.soreness_level)):
                if value is not None:
                    parts.append(f"{label} {value}/5")
            if checkin.pain_level:
                parts.append(f"pain {checkin.pain_level}/10")
            lines.append("Check-in: " + (", ".join(parts) if parts else "recorded without measurements") + ".")
        else:
            lines.append("No check-in recorded.")
        for result in performance:
            lines.append(_performance_line(result))
        lines.append("Tomorrow: " + RECOMMENDATIONS[readiness.decision])
        return " ".join(lines)


def _performance_line(result: dict) -> str:
    kind = result["kind"].replace("_", " ")
    latest = result.get("latest")
    if not latest:
        return f"{kind.capitalize()}: no comparable measurement."
    if result["kind"] in ("run", "sprint"):
        value = f"{latest['value']} s over {result['reference']['distance_m']:g} m"
        pace = pace_seconds_per_km(result["reference"]["distance_m"], latest["value"])
        if pace and result["kind"] == "run":
            value += f" ({int(pace // 60)}:{int(pace % 60):02d} per km)"
    else:
        value = f"{latest['value']} cm"
    comparison = result["comparison"]
    if not comparison:
        return f"{kind.capitalize()}: {value}. First comparable measurement, so no change to report yet."
    if comparison["within_noise"]:
        verdict = "no clear change (within measurement error)"
    else:
        verdict = "improved" if comparison["improved"] else "not improved"
    return f"{kind.capitalize()}: {value}, {verdict} vs {comparison['baseline_value']} on {result['baseline']['date']}."
