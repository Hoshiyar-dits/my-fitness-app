from datetime import date
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

class ComparisonPoint(BaseModel):
    date: date
    value: float
    distance_m: Optional[float] = None
    pace_seconds_per_km: Optional[float] = None
    speed_m_per_s: Optional[float] = None
    technique: Optional[str] = None

class Comparison(BaseModel):
    baseline_value: float
    latest_value: float
    change: float
    change_pct: Optional[float]
    improved: Optional[bool]  # None when the change is within measurement error
    within_noise: bool

class PerformanceComparison(BaseModel):
    """Best result of the first comparable session vs best of the latest one.
    Times in seconds (lower is better), jumps in centimetres (higher is better)."""
    kind: str
    reference: Dict[str, Any]
    sessions: int
    baseline: Optional[ComparisonPoint] = None
    latest: Optional[ComparisonPoint] = None
    comparison: Optional[Comparison]
    notes: List[str]

class MeasurementTrend(BaseModel):
    kind: str
    readings: int
    first_avg: Optional[float]
    last_avg: Optional[float]
    change: Optional[float]
    reliable: bool
    within_noise: Optional[bool]
    notes: List[str]
    method: Optional[str] = None
