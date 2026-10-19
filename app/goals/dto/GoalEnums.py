from enum import Enum

class GoalType(str, Enum):
    running_time = "running_time"
    sprint_time = "sprint_time"
    long_jump = "long_jump"
    high_jump = "high_jump"
    body_weight = "body_weight"
    body_fat = "body_fat"

class GoalStatus(str, Enum):
    active = "active"
    achieved = "achieved"
    abandoned = "abandoned"
    expired = "expired"

# Each goal type has exactly one unit, so two values of the same goal type are always comparable.
GOAL_UNITS = {
    GoalType.running_time: "s",
    GoalType.sprint_time: "s",
    GoalType.long_jump: "cm",
    GoalType.high_jump: "cm",
    GoalType.body_weight: "kg",
    GoalType.body_fat: "pct",
}
TIMED_GOALS = {GoalType.running_time, GoalType.sprint_time}
JUMP_GOALS = {GoalType.long_jump, GoalType.high_jump}

# which performance activity type feeds which goal type
ACTIVITY_GOAL_TYPES = {
    "run": GoalType.running_time,
    "sprint": GoalType.sprint_time,
    "long_jump": GoalType.long_jump,
    "high_jump": GoalType.high_jump,
}
