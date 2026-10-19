from enum import Enum

class ActivityType(str, Enum):
    run = "run"
    sprint = "sprint"
    long_jump = "long_jump"
    high_jump = "high_jump"

class MeasurementMethod(str, Enum):
    stopwatch = "stopwatch"
    gps_watch = "gps_watch"
    phone_app = "phone_app"
    track_timing = "track_timing"
    timing_gates = "timing_gates"
    tape_measure = "tape_measure"
    self_reported = "self_reported"
    other = "other"

class JumpTechnique(str, Enum):
    standing = "standing"
    run_up = "run_up"
    scissor = "scissor"
    fosbury_flop = "fosbury_flop"
    other = "other"
