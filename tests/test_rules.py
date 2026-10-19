"""Unit tests for the pure planning, readiness and metric functions."""
from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace
import pytest
from app.activities import metrics
from app.analysis.readiness import adjust_session, assess_readiness, safety_alert
from app.training import program_generator as gen
from app.training.exercise_catalog import HIGH_IMPACT_EXERCISES


def checkin(**overrides):
    values = dict(sleep_hours=Decimal("8"), sleep_quality=4, energy_level=4, fatigue_level=2, soreness_level=2,
                  pain_level=0, pain_location=None, warning_symptoms=[])
    values.update(overrides)
    return SimpleNamespace(**values)


def settings(level="intermediate", minutes=45, equipment=()):
    return gen.ProgramSettings(level=level, available_minutes=minutes, equipment=list(equipment),
                               run_assessment_m=gen.default_run_assessment_m(level), sprint_assessment_m=30)


# --- program generator -----------------------------------------------------------------

@pytest.mark.parametrize("level", ["beginner", "intermediate", "advanced"])
@pytest.mark.parametrize("equipment", [(), ("gym", "high_jump_setup", "track")])
def test_calendar_has_25_days_without_back_to_back_high_impact(level, equipment):
    sessions = gen.build_calendar(settings(level, equipment=equipment))
    assert [s.day_number for s in sessions] == list(range(1, 26))
    assert not gen.has_high_impact_stacking(sessions)
    types = {s.session_type for s in sessions}
    assert {"sprint", "endurance_run", "long_jump", "high_jump", "strength", "recovery", "rest", "assessment"} <= types


def test_calendar_repeats_baseline_assessments_at_the_end():
    sessions = gen.build_calendar(settings())
    titles = {s.day_number: s.title for s in sessions}
    assert titles[1].startswith("Baseline") and titles[23].startswith("Final")
    assert titles[3].startswith("Baseline") and titles[25].startswith("Final")
    run = lambda day: next(e for e in sessions[day - 1].exercises if e.name == "Run assessment")  # noqa: E731
    assert run(3).distance_m == run(13).distance_m == run(25).distance_m == 3000


def test_beginners_get_no_maximal_sprints():
    sessions = gen.build_calendar(settings("beginner"))
    names = {e.name for s in sessions for e in s.exercises}
    assert "Acceleration sprints" not in names and "Flying sprints" not in names and "Bounding" not in names
    assert "Strides" in names


def test_bar_jumps_only_with_high_jump_setup():
    without = {e.name for s in gen.build_calendar(settings()) for e in s.exercises}
    with_setup = {e.name for s in gen.build_calendar(settings(equipment=["high_jump_setup"])) for e in s.exercises}
    assert "Scissor jumps" not in without and "High jump assessment" not in without
    assert "Scissor jumps" in with_setup and "High jump assessment" in with_setup


def test_session_length_respects_available_time():
    sessions = gen.build_calendar(settings("advanced", minutes=20))
    assert all(s.minutes <= 30 for s in sessions)  # recovery sessions are a fixed 30 min of easy movement
    assert all(s.minutes <= 20 for s in sessions if s.session_type not in ("recovery", "rest"))


# --- readiness ---------------------------------------------------------------------------

def test_no_checkin_is_proceed_with_caution():
    assert assess_readiness(None).decision == "proceed_with_caution"


def test_good_checkin_proceeds():
    assert assess_readiness(checkin()).decision == "proceed"


@pytest.mark.parametrize("symptom", ["chest_pain", "dizziness", "fainting"])
def test_warning_symptoms_stop_training(symptom):
    result = assess_readiness(checkin(warning_symptoms=[symptom]))
    assert result.decision == "stop"
    assert "medical" in result.safety_message


def test_significant_pain_means_recovery_and_mild_pain_removes_impact():
    severe = assess_readiness(checkin(pain_level=6, pain_location="knee"))
    assert severe.decision == "recovery" and severe.avoid_high_impact and severe.safety_message
    mild = assess_readiness(checkin(pain_level=2))
    assert mild.decision == "modify" and mild.avoid_high_impact


def test_recurring_pain_recommends_assessment():
    result = assess_readiness(checkin(pain_level=2), [checkin(pain_level=2), checkin(pain_level=3)])
    assert result.safety_message is not None


def test_fatigue_flags():
    assert assess_readiness(checkin(sleep_hours=Decimal("5"))).decision == "modify"
    assert assess_readiness(checkin(sleep_hours=Decimal("5"), fatigue_level=5)).decision == "recovery"


def test_safety_alert():
    assert safety_alert([], 0) is None
    assert safety_alert(["chest_pain"], None) is not None
    assert safety_alert([], 5) is not None


# --- plan adjustment --------------------------------------------------------------------

def _sprint():
    return gen.sprint_session(settings("advanced"), 1.0)


def test_proceed_keeps_session_unchanged():
    assert adjust_session(_sprint(), assess_readiness(checkin()), high_impact_today=False) is None


def test_missed_workout_never_increases_load():
    """A skipped day leaves readiness unchanged, and adjustments only ever reduce volume."""
    spec = _sprint()
    adjusted, _ = adjust_session(spec, assess_readiness(checkin(fatigue_level=5)), high_impact_today=False)
    planned = sum((e.sets or 0) for e in spec.exercises)
    assert sum((e.sets or 0) for e in adjusted.exercises) <= planned


def test_modify_reduces_volume_and_intensity():
    spec = _sprint()
    adjusted, reasons = adjust_session(spec, assess_readiness(checkin(sleep_hours=Decimal("5"))), high_impact_today=False)
    assert adjusted.intensity == "moderate" and spec.intensity == "high"
    assert sum(e.sets or 0 for e in adjusted.exercises) < sum(e.sets or 0 for e in spec.exercises)
    assert reasons


def test_pain_removes_high_impact_exercises():
    adjusted, _ = adjust_session(_sprint(), assess_readiness(checkin(pain_level=2)), high_impact_today=False)
    assert not any(e.name in HIGH_IMPACT_EXERCISES for e in adjusted.exercises)


def test_back_to_back_high_impact_is_prevented():
    adjusted, reasons = adjust_session(_sprint(), assess_readiness(checkin()), high_impact_today=True)
    assert not adjusted.is_high_impact
    assert any("back-to-back" in r for r in reasons)


def test_stop_replaces_with_rest_and_recovery_postpones_assessment():
    stop, _ = adjust_session(_sprint(), assess_readiness(checkin(warning_symptoms=["dizziness"])), False)
    assert stop.session_type == "rest" and not stop.exercises
    assessment = gen.jump_sprint_assessment(settings(), final=False)
    assessment.day_number = 23
    recovery, reasons = adjust_session(assessment, assess_readiness(checkin(pain_level=7)), False)
    assert recovery.session_type == "recovery" and recovery.day_number == 23
    assert any("postponed" in r for r in reasons)


def test_rest_days_are_never_adjusted():
    assert adjust_session(gen.rest_session(), assess_readiness(checkin(pain_level=8)), True) is None


# --- metrics -------------------------------------------------------------------------------

def act(kind, day, value, distance=None, technique=None, method="stopwatch", id=None):
    timed = kind in ("run", "sprint")
    return SimpleNamespace(id=id, activity_type=kind, activity_date=day, measurement_method=method, technique=technique,
                           distance_m=Decimal(str(distance)) if distance else None,
                           elapsed_seconds=Decimal(str(value)) if timed else None,
                           jump_cm=None if timed else Decimal(str(value)))


def test_pace_and_speed():
    assert metrics.pace_seconds_per_km(3000, 900) == 300.0
    assert metrics.speed_m_per_s(100, 12.5) == 8.0
    assert metrics.pace_seconds_per_km(None, 900) is None
    assert metrics.pace_seconds_per_km(0, 900) is None


def test_runs_over_different_distances_are_not_compared():
    d = date(2026, 10, 1)
    rows = [act("run", d, 900, 3000), act("run", d + timedelta(days=5), 300, 1000)]
    result = metrics.performance_comparison(rows, "run", reference_distance_m=3000)
    assert result["sessions"] == 1 and result["comparison"] is None


def test_run_improvement_uses_best_time_of_each_day():
    d = date(2026, 10, 1)
    rows = [act("run", d, 900, 3000), act("run", d, 880, 3000), act("run", d + timedelta(days=20), 840, 3005)]
    result = metrics.performance_comparison(rows, "run", reference_distance_m=3000)
    assert result["comparison"]["baseline_value"] == 880
    assert result["comparison"]["latest_value"] == 840
    assert result["comparison"]["improved"] is True


def test_small_changes_are_within_noise():
    d = date(2026, 10, 1)
    rows = [act("long_jump", d, 200, technique="standing"), act("long_jump", d + timedelta(days=10), 203, technique="standing")]
    result = metrics.performance_comparison(rows, "long_jump", technique="standing")
    assert result["comparison"]["within_noise"] is True and result["comparison"]["improved"] is None


def test_jumps_with_other_technique_are_excluded_and_method_change_noted():
    d = date(2026, 10, 1)
    rows = [act("long_jump", d, 200, technique="standing", method="tape_measure"),
            act("long_jump", d + timedelta(days=3), 400, technique="run_up"),
            act("long_jump", d + timedelta(days=9), 215, technique="standing", method="self_reported")]
    result = metrics.performance_comparison(rows, "long_jump", technique="standing")
    assert result["comparison"]["latest_value"] == 215
    assert any("different methods" in n for n in result["notes"])


def test_missing_measurements_do_not_break_comparisons():
    assert metrics.performance_comparison([], "run")["comparison"] is None
    trend = metrics.measurement_trend([(date(2026, 10, 1), None)], "body_weight")
    assert trend["change"] is None and trend["reliable"] is False


def test_weight_trend_averages_and_reliability():
    d = date(2026, 10, 1)
    readings = [(d, 82.0), (d + timedelta(days=1), 81.6), (d + timedelta(days=20), 80.6), (d + timedelta(days=21), 80.2)]
    trend = metrics.measurement_trend(readings, "body_weight")
    assert trend["first_avg"] == 81.8 and trend["last_avg"] == 80.4 and trend["change"] == -1.4
    assert trend["reliable"] is True and trend["within_noise"] is False
    short = metrics.measurement_trend(readings[:2], "body_weight")
    assert short["reliable"] is False
