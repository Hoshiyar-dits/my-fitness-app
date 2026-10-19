"""Deterministic 25-day calendar generator. Pure functions, no database access.

Layout (day numbers are 1-based):
  1  baseline jump + sprint assessment      2  recovery      3  baseline run assessment
  4-21  repeating 7-day microcycle: strength, long jump, endurance, recovery, sprint, rest, high jump
        (high-impact days are always separated by at least one low-impact day)
        13 is replaced by a mid-cycle running check
  22 rest   23 final jump + sprint assessment   24 recovery   25 final run assessment

Assessments repeat the baseline protocol (same distances, technique and order) so results are comparable.
"""
from copy import deepcopy
from dataclasses import dataclass, field
from typing import List, Optional
from app.training.exercise_catalog import HIGH_IMPACT_EXERCISES

PROGRAM_DAYS = 25

LEVELS = {
    "beginner": dict(sets=2, sprint_reps=4, sprint_m=20, jump_reps=3, run_min=20, interval_reps=4, interval_m=400, minutes=35, run_assessment_m=1600),
    "intermediate": dict(sets=3, sprint_reps=5, sprint_m=30, jump_reps=4, run_min=30, interval_reps=5, interval_m=600, minutes=45, run_assessment_m=3000),
    "advanced": dict(sets=4, sprint_reps=6, sprint_m=40, jump_reps=5, run_min=40, interval_reps=6, interval_m=800, minutes=60, run_assessment_m=5000),
}
DEFAULT_SPRINT_ASSESSMENT_M = 30

PHASE_VOLUME = {"foundation": 1.0, "development": 1.2, "taper": 0.7}
MICROCYCLE = ["strength", "long_jump", "endurance", "recovery", "sprint", "rest", "high_jump"]
INTENSITY_ORDER = ["low", "moderate", "high"]

WARM_UP = "10 min: easy jog or brisk walk, dynamic mobility, then 2-3 gradual build-ups."
COOL_DOWN = "5-10 min easy walk or jog, then gentle stretching."
PAIN_NOTE = "Stop and rest if you feel sharp or increasing pain."


@dataclass
class ExerciseSpec:
    name: str
    sets: Optional[int] = None
    reps: Optional[int] = None
    distance_m: Optional[float] = None
    duration_seconds: Optional[int] = None
    rest_seconds: Optional[int] = None
    effort: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class SessionSpec:
    session_type: str
    title: str
    intensity: str
    minutes: int
    description: str
    exercises: List[ExerciseSpec] = field(default_factory=list)
    day_number: Optional[int] = None
    phase: Optional[str] = None
    warm_up: Optional[str] = WARM_UP
    cool_down: Optional[str] = COOL_DOWN

    @property
    def is_high_impact(self) -> bool:
        return any(e.name in HIGH_IMPACT_EXERCISES for e in self.exercises)


@dataclass
class ProgramSettings:
    level: str
    available_minutes: int
    equipment: List[str]
    run_assessment_m: float
    sprint_assessment_m: float


def default_run_assessment_m(level: str) -> int:
    return LEVELS[level]["run_assessment_m"]


def phase_for_day(day: int) -> str:
    if day <= 3:
        return "baseline"
    if day <= 10:
        return "foundation"
    if day <= 18:
        return "development"
    if day <= 22:
        return "taper"
    return "final_assessment"


def build_calendar(settings: ProgramSettings) -> List[SessionSpec]:
    sessions = []
    for day in range(1, PROGRAM_DAYS + 1):
        session = _session_for_day(day, settings)
        session.day_number = day
        session.phase = phase_for_day(day)
        sessions.append(session)
    return sessions


def has_high_impact_stacking(sessions: List[SessionSpec]) -> bool:
    return any(a.is_high_impact and b.is_high_impact for a, b in zip(sessions, sessions[1:]))


def _session_for_day(day: int, s: ProgramSettings) -> SessionSpec:
    if day in (1, 23):
        return jump_sprint_assessment(s, final=day == 23)
    if day in (3, 25):
        return run_assessment(s, label="Final" if day == 25 else "Baseline")
    if day == 13:
        return run_assessment(s, label="Mid-cycle")
    if day in (2, 24):
        return recovery_session()
    if day == 22:
        return rest_session()

    kind = MICROCYCLE[(day - 4) % 7]
    week = (day - 4) // 7
    volume = PHASE_VOLUME[phase_for_day(day)]
    builders = {
        "strength": lambda: strength_session(s, volume),
        "long_jump": lambda: long_jump_session(s, volume),
        "endurance": lambda: endurance_session(s, volume, week),
        "recovery": recovery_session,
        "sprint": lambda: sprint_session(s, volume),
        "rest": rest_session,
        "high_jump": lambda: high_jump_session(s, volume),
    }
    return builders[kind]()


def _cfg(s: ProgramSettings) -> dict:
    return LEVELS[s.level]


def _scale(n: int, volume: float, s: ProgramSettings) -> int:
    # fewer sets when the user has less time than the level's typical session length
    time_factor = min(1.0, s.available_minutes / _cfg(s)["minutes"])
    return max(1, round(n * volume * time_factor))


def _minutes(s: ProgramSettings, volume: float = 1.0) -> int:
    return max(15, min(s.available_minutes, round(_cfg(s)["minutes"] * volume)))


def _has(s: ProgramSettings, item: str) -> bool:
    if item == "dumbbells":
        return "dumbbells" in s.equipment or "gym" in s.equipment
    return item in s.equipment


def strength_session(s: ProgramSettings, volume: float) -> SessionSpec:
    sets = _scale(_cfg(s)["sets"], volume, s)
    loaded = _has(s, "dumbbells")
    exercises = [
        ExerciseSpec("Goblet squat" if loaded else "Bodyweight squat", sets=sets, reps=8 if loaded else 12, rest_seconds=90, effort="2-3 reps left in reserve"),
        ExerciseSpec("Romanian deadlift" if loaded else "Glute bridge", sets=sets, reps=8 if loaded else 12, rest_seconds=90, effort="2-3 reps left in reserve"),
        ExerciseSpec("Split squat", sets=sets, reps=8, rest_seconds=60, notes="Reps per leg"),
        ExerciseSpec("Calf raises", sets=sets, reps=12, rest_seconds=45),
        ExerciseSpec("Plank", sets=sets, duration_seconds=30, rest_seconds=45),
        ExerciseSpec("Hip mobility flow", sets=1, duration_seconds=300),
    ]
    return SessionSpec("strength", "Strength and mobility", "moderate", _minutes(s, volume),
                       "Lower-body and trunk strength to support sprinting and jumping. " + PAIN_NOTE, exercises)


def long_jump_session(s: ProgramSettings, volume: float) -> SessionSpec:
    cfg = _cfg(s)
    exercises = [
        ExerciseSpec("A-skips", sets=2, distance_m=20, rest_seconds=60),
        ExerciseSpec("Pop-up jumps", sets=_scale(cfg["jump_reps"], volume, s), reps=1, rest_seconds=90,
                     effort="Technique focus, about 80%", notes="3-5 step approach, land on both feet on a soft surface"),
        ExerciseSpec("Standing long jump", sets=_scale(2, volume, s), reps=3, rest_seconds=120, effort="About 80%, focus on arm swing and landing"),
    ]
    if s.level != "beginner":
        exercises.append(ExerciseSpec("Bounding", sets=_scale(3, volume, s), distance_m=20, rest_seconds=120, effort="Controlled, not maximal"))
    exercises.append(ExerciseSpec("Easy run", duration_seconds=600, effort="Conversational"))
    return SessionSpec("long_jump", "Long jump technique", "moderate", _minutes(s, volume),
                       "Low-volume take-off and landing practice while fresh. Quality over quantity. " + PAIN_NOTE, exercises)


def endurance_session(s: ProgramSettings, volume: float, week: int) -> SessionSpec:
    cfg = _cfg(s)
    minutes = _minutes(s, volume)
    # running time fits inside the session after warm-up and cool-down
    run_seconds = max(600, min(round(cfg["run_min"] * 60 * volume), (minutes - 10) * 60))
    if s.level == "beginner" or week % 2 == 0:
        exercises = [ExerciseSpec("Easy run", duration_seconds=run_seconds, effort="Conversational, walk breaks allowed")]
        return SessionSpec("endurance_run", "Easy aerobic run", "low", minutes,
                           "Builds aerobic base with low injury risk. Keep it easy.", exercises)
    if s.level == "intermediate":
        exercises = [ExerciseSpec("Tempo run", duration_seconds=max(600, round(run_seconds * 0.6)), effort="Comfortably hard")]
        return SessionSpec("endurance_run", "Tempo run", "moderate", minutes,
                           "Sustained comfortably hard running to raise the pace you can hold.", exercises)
    exercises = [ExerciseSpec("Run intervals", sets=_scale(cfg["interval_reps"], volume, s), distance_m=cfg["interval_m"],
                              rest_seconds=120, effort="Around 5 km race pace")]
    return SessionSpec("endurance_run", "Running intervals", "high", minutes,
                       "Repeated efforts near 5 km pace with easy jog recoveries.", exercises)


def sprint_session(s: ProgramSettings, volume: float) -> SessionSpec:
    cfg = _cfg(s)
    exercises = [ExerciseSpec("A-skips", sets=2, distance_m=20, rest_seconds=60)]
    if s.level == "beginner":
        # beginners build sprint tolerance with sub-maximal strides, never all-out sprints
        exercises.append(ExerciseSpec("Strides", sets=_scale(cfg["sprint_reps"], volume, s), distance_m=60, rest_seconds=90, effort="70-80%, relaxed"))
        intensity = "moderate"
    else:
        exercises.append(ExerciseSpec("Acceleration sprints", sets=_scale(cfg["sprint_reps"], volume, s), distance_m=cfg["sprint_m"],
                                      rest_seconds=120, effort="About 90%, not all-out"))
        if s.level == "advanced":
            exercises.append(ExerciseSpec("Flying sprints", sets=_scale(3, volume, s), distance_m=20, rest_seconds=180, effort="About 95%"))
        intensity = "high"
    return SessionSpec("sprint", "Sprint mechanics and acceleration", intensity, _minutes(s, volume),
                       "Short, fast, fully recovered efforts. Stop the session if your speed drops noticeably. " + PAIN_NOTE, exercises)


def high_jump_session(s: ProgramSettings, volume: float) -> SessionSpec:
    sets = _scale(_cfg(s)["sets"], volume, s)
    exercises = [
        ExerciseSpec("High jump approach curve runs", sets=4, rest_seconds=60, effort="About 70%"),
        ExerciseSpec("High jump take-off drill", sets=sets, reps=4, rest_seconds=90, effort="Technique focus"),
    ]
    if _has(s, "high_jump_setup"):
        exercises.append(ExerciseSpec("Scissor jumps", sets=sets, reps=3, rest_seconds=120, effort="Low bar, technique only"))
        if s.level != "beginner":
            exercises.append(ExerciseSpec("Fosbury flop technique jumps", sets=2, reps=3, rest_seconds=150, effort="Short approach, low bar"))
    exercises += [
        ExerciseSpec("Calf raises", sets=2, reps=12, rest_seconds=45),
        ExerciseSpec("Glute bridge", sets=2, reps=12, rest_seconds=45),
    ]
    description = "High jump approach and take-off technique at low bar heights."
    if not _has(s, "high_jump_setup"):
        description += " No bar or landing mat available, so this session uses bar-free drills only."
    return SessionSpec("high_jump", "High jump technique", "moderate", _minutes(s, volume), description + " " + PAIN_NOTE, exercises)


def recovery_session() -> SessionSpec:
    exercises = [
        ExerciseSpec("Easy walk", duration_seconds=1200, effort="Easy"),
        ExerciseSpec("Hip mobility flow", sets=1, duration_seconds=300),
        ExerciseSpec("Ankle and calf mobility", sets=1, duration_seconds=300),
    ]
    return SessionSpec("recovery", "Active recovery", "low", 30,
                       "Gentle movement to help recovery. Should feel easier at the end than at the start.", exercises,
                       warm_up=None, cool_down=None)


def rest_session() -> SessionSpec:
    return SessionSpec("rest", "Rest day", "low", 0,
                       "Full rest. Light walking is fine. Remember your daily check-in.", [], warm_up=None, cool_down=None)


def jump_sprint_assessment(s: ProgramSettings, final: bool) -> SessionSpec:
    attempts = 2 if s.level == "beginner" else 3
    effort = "Fast but controlled (about 90%)" if s.level == "beginner" else "Best effort"
    exercises = [
        ExerciseSpec("A-skips", sets=2, distance_m=20, rest_seconds=60),
        ExerciseSpec("Long jump assessment", sets=3, reps=1, rest_seconds=120, effort=effort,
                     notes="Standing long jump, measured from the take-off line. Log each attempt with technique 'standing'."),
        ExerciseSpec("Sprint assessment", sets=attempts, distance_m=float(s.sprint_assessment_m), rest_seconds=180, effort=effort,
                     notes="Standing start, same surface and timing method as the baseline. Log each attempt."),
    ]
    if _has(s, "high_jump_setup"):
        exercises.insert(2, ExerciseSpec("High jump assessment", sets=5, reps=1, rest_seconds=150, effort=effort,
                                         notes="Start well below your best and raise the bar gradually. Log your best clearance."))
    label = "Final" if final else "Baseline"
    return SessionSpec("assessment", f"{label} jump and sprint assessment", "moderate" if s.level == "beginner" else "high",
                       _minutes(s), "Measured attempts using exactly the same protocol as every other assessment, "
                       "so results are comparable. Jumps come first while you are fresh. " + PAIN_NOTE, exercises)


def run_assessment(s: ProgramSettings, label: str) -> SessionSpec:
    exercises = [ExerciseSpec("Run assessment", sets=1, distance_m=float(s.run_assessment_m),
                              effort="Steady, sustainable best effort" if s.level == "beginner" else "Best sustainable effort",
                              notes="Same route/surface and timing method as the baseline. Log total time and splits if you have them.")]
    return SessionSpec("assessment", f"{label} running assessment", "moderate" if s.level == "beginner" else "high",
                       _minutes(s), f"Timed {int(s.run_assessment_m)} m run, used to compare endurance across the cycle.", exercises)


def lower_intensity(intensity: str) -> str:
    index = INTENSITY_ORDER.index(intensity) if intensity in INTENSITY_ORDER else 1
    return INTENSITY_ORDER[max(0, index - 1)]


def reduced_volume(spec: SessionSpec, factor: float = 0.7) -> SessionSpec:
    reduced = deepcopy(spec)
    for exercise in reduced.exercises:
        if exercise.sets and exercise.sets > 1:
            exercise.sets = max(1, round(exercise.sets * factor))
        if exercise.duration_seconds and exercise.name not in ("Hip mobility flow", "Ankle and calf mobility"):
            exercise.duration_seconds = round(exercise.duration_seconds * factor)
    reduced.intensity = lower_intensity(spec.intensity)
    reduced.minutes = max(15, round(spec.minutes * 0.8)) if spec.minutes else spec.minutes
    return reduced


def without_high_impact(spec: SessionSpec) -> SessionSpec:
    low = deepcopy(spec)
    low.exercises = [e for e in low.exercises if e.name not in HIGH_IMPACT_EXERCISES]
    names = {e.name for e in low.exercises}
    for name in ("Hip mobility flow", "Ankle and calf mobility"):
        if name not in names:
            low.exercises.append(ExerciseSpec(name, sets=1, duration_seconds=300))
    low.title = f"Low-impact version: {spec.title}"
    low.intensity = lower_intensity(spec.intensity)
    return low
