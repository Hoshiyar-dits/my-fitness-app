from enum import Enum

class WarningSymptom(str, Enum):
    """Symptoms that stop training recommendations and trigger advice to seek medical assessment."""
    chest_pain = "chest_pain"
    dizziness = "dizziness"
    fainting = "fainting"
    shortness_of_breath = "shortness_of_breath"
    heart_palpitations = "heart_palpitations"
    severe_headache = "severe_headache"
    other_concerning = "other_concerning"
