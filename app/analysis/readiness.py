"""Readiness and plan-adjustment rules. Pure functions: the inputs are check-in-like objects
(anything with the DailyCheckin attributes) and SessionSpecs, so they are easy to test.

Decisions, least to most conservative:
  proceed               train as planned
  proceed_with_caution  no check-in, so recovery is unknown; keep the plan but say so
  modify                reduce volume and intensity, and drop high-impact work if there is pain
  recovery              replace the session with active recovery
  stop                  warning symptoms: no training, recommend medical assessment
"""
from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Tuple
from app.training.program_generator import SessionSpec, recovery_session, rest_session, reduced_volume, without_high_impact

DECISIONS = ["proceed", "proceed_with_caution", "modify", "recovery", "stop"]

URGENT_SYMPTOMS = {"chest_pain", "fainting", "shortness_of_breath"}
STOP_MESSAGE = (
    "You reported a warning symptom. Do not train today, and get a medical assessment before training again. "
    "If you have chest pain, have fainted, or are struggling to breathe, contact emergency services now."
)
PAIN_MESSAGE = (
    "Do not train through significant pain. If the pain is severe, keeps coming back or does not ease with rest, "
    "have it assessed by a doctor or physiotherapist."
)


@dataclass
class Readiness:
    decision: str
    reasons: List[str] = field(default_factory=list)
    safety_message: Optional[str] = None
    avoid_high_impact: bool = False


def safety_alert(warning_symptoms: Optional[Iterable[str]], pain_level: Optional[int]) -> Optional[str]:
    if warning_symptoms:
        return STOP_MESSAGE
    if pain_level is not None and pain_level >= 4:
        return PAIN_MESSAGE
    return None


def _escalate(current: str, new: str) -> str:
    return new if DECISIONS.index(new) > DECISIONS.index(current) else current


def assess_readiness(checkin, recent_checkins: Iterable = ()) -> Readiness:
    """`checkin` is the latest check-in (or None), `recent_checkins` the ones from the previous few days."""
    if checkin is None:
        return Readiness("proceed_with_caution", ["No check-in recorded, so sleep, fatigue and pain are unknown."])

    result = Readiness("proceed")
    symptoms = list(checkin.warning_symptoms or [])
    if symptoms:
        result.decision = "stop"
        result.reasons.append(f"Warning symptoms reported: {', '.join(symptoms)}.")
        result.safety_message = STOP_MESSAGE
        result.avoid_high_impact = True
        return result

    pain = checkin.pain_level
    if pain is not None and pain >= 4:
        result.decision = _escalate(result.decision, "recovery")
        result.reasons.append(f"Pain reported at {pain}/10" + (f" ({checkin.pain_location})" if checkin.pain_location else "") + ".")
        result.safety_message = PAIN_MESSAGE
        result.avoid_high_impact = True
    elif pain is not None and pain >= 1:
        result.decision = _escalate(result.decision, "modify")
        result.reasons.append(f"Mild pain reported ({pain}/10), so high-impact work is removed.")
        result.avoid_high_impact = True

    recent_pain_days = sum(1 for c in recent_checkins if c.pain_level is not None and c.pain_level >= 1)
    if pain and recent_pain_days >= 2:
        result.reasons.append("Pain has been reported on several recent days.")
        result.safety_message = PAIN_MESSAGE

    flags = []
    if checkin.sleep_hours is not None and float(checkin.sleep_hours) < 6:
        flags.append(f"short sleep ({checkin.sleep_hours} h)")
    if checkin.sleep_quality is not None and checkin.sleep_quality <= 2:
        flags.append("poor sleep quality")
    if checkin.energy_level is not None and checkin.energy_level <= 2:
        flags.append("low energy")
    if checkin.fatigue_level is not None and checkin.fatigue_level >= 4:
        flags.append("high fatigue")
    if checkin.soreness_level is not None and checkin.soreness_level >= 4:
        flags.append("high muscle soreness")
    if len(flags) >= 2:
        result.decision = _escalate(result.decision, "recovery")
        result.reasons.append("Several recovery warning signs: " + ", ".join(flags) + ".")
    elif flags:
        result.decision = _escalate(result.decision, "modify")
        result.reasons.append("Recovery warning sign: " + flags[0] + ", so volume and intensity are reduced.")

    if result.decision == "proceed":
        result.reasons.append("Check-in shows no recovery concerns.")
    return result


def adjust_session(spec: SessionSpec, readiness: Readiness, high_impact_today: bool) -> Optional[Tuple[SessionSpec, List[str]]]:
    """Returns (adjusted session, reasons), or None when the planned session should go ahead unchanged.
    Never adds volume or intensity, including after a missed workout."""
    if spec.session_type == "rest":
        return None

    if readiness.decision == "stop":
        adjusted = rest_session()
        adjusted.description = "No training. " + STOP_MESSAGE
        return _keep_calendar_slot(adjusted, spec), ["Training replaced with rest because of reported warning symptoms."]

    if readiness.decision == "recovery":
        adjusted = recovery_session()
        reasons = ["Session replaced with active recovery: " + " ".join(readiness.reasons)]
        if spec.session_type == "assessment":
            reasons.append("The assessment is postponed so it can be done fresh and stay comparable with the baseline.")
        return _keep_calendar_slot(adjusted, spec), reasons

    adjusted, reasons = spec, []
    if readiness.decision == "modify":
        adjusted = reduced_volume(adjusted)
        reasons.append("Volume reduced by about 30% and intensity lowered: " + " ".join(readiness.reasons))

    if spec.is_high_impact and (readiness.avoid_high_impact or high_impact_today):
        if spec.session_type == "assessment":
            adjusted = recovery_session()
            reasons.append("The assessment is postponed so it can be done fresh and stay comparable with the baseline.")
        else:
            adjusted = without_high_impact(adjusted)
        if high_impact_today and not readiness.avoid_high_impact:
            reasons.append("High-impact work was done today, so tomorrow's high-impact exercises are removed to avoid back-to-back impact days.")
        else:
            reasons.append("High-impact exercises (sprints, jumps) removed because of reported pain.")

    if not reasons:
        return None
    return _keep_calendar_slot(adjusted, spec), reasons


def _keep_calendar_slot(adjusted: SessionSpec, original: SessionSpec) -> SessionSpec:
    adjusted.day_number = original.day_number
    adjusted.phase = original.phase
    return adjusted
