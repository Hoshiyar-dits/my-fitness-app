from enum import Enum

class WorkoutType(str, Enum):
    cardio = "cardio"
    strength = "strength"
    flexibility = "flexibility"
    hiit = "hiit"
    sports = "sports"
    other = "other"

class Intensity(str, Enum):
    low = "low"
    moderate = "moderate"
    high = "high"
