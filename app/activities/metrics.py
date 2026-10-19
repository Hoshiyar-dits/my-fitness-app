"""Derived performance metrics and comparisons. The single place these numbers are calculated.

Units: distances in metres, times in seconds, jumps in centimetres, body weight in kg, body fat in %.
A comparison is only made between measurements that are comparable: runs and sprints over the same
distance (within 1%), and jumps of the same type with the same technique. Changes smaller than typical
measurement error are reported as `within_noise`, not as improvement.
"""
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from typing import Iterable, List, Optional, Sequence, Tuple

DISTANCE_TOLERANCE = 0.01

# Rough typical measurement error. Below these, a change could just be timing/measuring noise.
NOISE = {
    "run": ("pct", 2.0),  # hand / GPS timing over a comparable distance
    "sprint": ("pct", 3.0),  # hand timing over short sprints is imprecise
    "long_jump": ("abs", 5.0),  # cm
    "high_jump": ("abs", 3.0),  # cm
    "body_weight": ("abs", 0.5),  # kg, normal day-to-day fluctuation is larger than this
    "body_fat": ("abs", 1.0),  # percentage points
}
TIMED = {"run", "sprint"}


def _f(value) -> Optional[float]:
    return float(value) if value is not None else None


def pace_seconds_per_km(distance_m, elapsed_seconds) -> Optional[float]:
    distance, elapsed = _f(distance_m), _f(elapsed_seconds)
    if not distance or not elapsed or distance <= 0 or elapsed <= 0:
        return None
    return round(elapsed / distance * 1000, 1)


def speed_m_per_s(distance_m, elapsed_seconds) -> Optional[float]:
    distance, elapsed = _f(distance_m), _f(elapsed_seconds)
    if not distance or not elapsed or distance <= 0 or elapsed <= 0:
        return None
    return round(distance / elapsed, 2)


def same_distance(a, b) -> bool:
    a, b = _f(a), _f(b)
    if not a or not b:
        return False
    return abs(a - b) / max(a, b) <= DISTANCE_TOLERANCE


def activity_value(activity) -> Optional[float]:
    if activity.activity_type in TIMED:
        return _f(activity.elapsed_seconds)
    return _f(activity.jump_cm)


def _within_noise(kind: str, baseline: float, change: float) -> bool:
    mode, threshold = NOISE[kind]
    if mode == "pct":
        return abs(change) / baseline * 100 < threshold
    return abs(change) < threshold


def compare(kind: str, baseline: float, latest: float, lower_is_better: bool) -> dict:
    change = latest - baseline
    within_noise = _within_noise(kind, baseline, change)
    improved = None if within_noise else ((change < 0) if lower_is_better else (change > 0))
    return {
        "baseline_value": round(baseline, 2),
        "latest_value": round(latest, 2),
        "change": round(change, 2),
        "change_pct": round(change / baseline * 100, 1) if baseline else None,
        "improved": improved,
        "within_noise": within_noise,
    }


def comparable_activities(activities: Sequence, kind: str, reference_distance_m=None, technique: Optional[str] = None) -> Tuple[list, dict]:
    """Filters to measurements comparable with the reference (defaults: the earliest measurement's distance / technique)."""
    rows = sorted((a for a in activities if a.activity_type == kind and activity_value(a) is not None),
                  key=lambda a: (a.activity_date, a.id or 0))
    if not rows:
        return [], {}
    if kind in TIMED:
        reference = reference_distance_m if reference_distance_m is not None else rows[0].distance_m
        rows = [a for a in rows if same_distance(a.distance_m, reference)]
        return rows, {"distance_m": _f(reference)}
    reference = technique if technique is not None else rows[0].technique
    rows = [a for a in rows if a.technique == reference]
    return rows, {"technique": reference}


def best_per_day(rows: Iterable, kind: str) -> List[Tuple[date, float, object]]:
    by_day = defaultdict(list)
    for activity in rows:
        by_day[activity.activity_date].append(activity)
    best = []
    for day in sorted(by_day):
        pick = (min if kind in TIMED else max)(by_day[day], key=activity_value)
        best.append((day, activity_value(pick), pick))
    return best


def performance_comparison(activities: Sequence, kind: str, reference_distance_m=None, technique: Optional[str] = None) -> dict:
    """Baseline (first comparable session) vs latest comparable session, using each session's best result."""
    rows, reference = comparable_activities(activities, kind, reference_distance_m, technique)
    sessions = best_per_day(rows, kind)
    result = {"kind": kind, "reference": reference, "sessions": len(sessions), "comparison": None, "notes": []}
    if not sessions:
        result["notes"].append("No comparable measurements recorded yet.")
        return result
    first_day, first_value, first = sessions[0]
    last_day, last_value, last = sessions[-1]
    result["baseline"] = {"date": first_day, "value": round(first_value, 2), **_derived(first)}
    result["latest"] = {"date": last_day, "value": round(last_value, 2), **_derived(last)}
    if len(sessions) < 2:
        result["notes"].append("Only one comparable session so far, so there is no change to report yet.")
        return result
    result["comparison"] = compare(kind, first_value, last_value, lower_is_better=kind in TIMED)
    if first.measurement_method != last.measurement_method:
        result["notes"].append("Baseline and latest were measured with different methods, so the comparison is less reliable.")
    if result["comparison"]["within_noise"]:
        result["notes"].append("The change is within typical measurement error, so treat it as no clear change.")
    if kind in ("long_jump", "high_jump"):
        result["notes"].append("Jump results vary with technique, fatigue and surface. Compare sessions done under similar conditions.")
    return result


def _derived(activity) -> dict:
    if activity.activity_type not in TIMED:
        return {"technique": activity.technique}
    return {
        "distance_m": _f(activity.distance_m),
        "pace_seconds_per_km": pace_seconds_per_km(activity.distance_m, activity.elapsed_seconds),
        "speed_m_per_s": speed_m_per_s(activity.distance_m, activity.elapsed_seconds),
    }


def measurement_trend(readings: Sequence[Tuple[date, object]], kind: str, window_days: int = 4, min_span_days: int = 7) -> dict:
    """Compares the average of the first few days with the average of the last few days, rather than two
    single readings, because single weigh-ins swing with water, food and time of day."""
    points = sorted((d, float(v)) for d, v in readings if v is not None)
    result = {"kind": kind, "readings": len(points), "first_avg": None, "last_avg": None, "change": None,
              "reliable": False, "within_noise": None, "notes": []}
    if len(points) < 2:
        result["notes"].append("Not enough readings to show a trend.")
        return result
    first_day, last_day = points[0][0], points[-1][0]
    span = (last_day - first_day).days
    first = [v for d, v in points if d <= first_day + timedelta(days=window_days - 1)]
    last = [v for d, v in points if d >= last_day - timedelta(days=window_days - 1)]
    result["first_avg"] = round(sum(first) / len(first), 2)
    result["last_avg"] = round(sum(last) / len(last), 2)
    result["change"] = round(result["last_avg"] - result["first_avg"], 2)
    result["within_noise"] = abs(result["change"]) < NOISE[kind][1]
    if span < min_span_days:
        result["notes"].append(f"Readings only cover {span} days. Trends need at least {min_span_days}.")
    elif len(first) < 2 or len(last) < 2:
        result["notes"].append("Fewer than two readings at the start or end, so this trend is rough.")
    else:
        result["reliable"] = True
    if result["within_noise"]:
        result["notes"].append("The change is within normal day-to-day variation.")
    if kind == "body_fat":
        result["notes"].append("Body-fat readings from consumer devices are estimates. Only the trend from the same method is meaningful.")
    return result


def to_decimal(value: Optional[float]) -> Optional[Decimal]:
    return Decimal(str(value)) if value is not None else None
