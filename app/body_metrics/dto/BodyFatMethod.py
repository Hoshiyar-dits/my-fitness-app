from enum import Enum

class BodyFatMethod(str, Enum):
    smart_scale = "smart_scale"
    calipers = "calipers"
    tape_formula = "tape_formula"
    dexa = "dexa"
    bod_pod = "bod_pod"
    other = "other"
