from enum import Enum

class ExperienceLevel(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"

class Equipment(str, Enum):
    track = "track"
    gym = "gym"
    dumbbells = "dumbbells"
    high_jump_setup = "high_jump_setup"  # bar (or elastic) and a proper landing mat
    sand_pit = "sand_pit"

class ProgramStatus(str, Enum):
    awaiting_clearance = "awaiting_clearance"
    active = "active"
    completed = "completed"
    cancelled = "cancelled"

class SessionType(str, Enum):
    sprint = "sprint"
    endurance_run = "endurance_run"
    long_jump = "long_jump"
    high_jump = "high_jump"
    strength = "strength"
    mobility = "mobility"
    recovery = "recovery"
    rest = "rest"
    assessment = "assessment"

class PlanSource(str, Enum):
    program_template = "program_template"  # generated with the 25-day program the user created
    rules = "rules"  # adaptive rules (POST /plans/tomorrow)
    ai_agent = "ai_agent"  # proposed during an AI chat
    user = "user"  # created by the user

class PlanStatus(str, Enum):
    proposed = "proposed"  # a suggestion only, not part of the user's plan until confirmed
    confirmed = "confirmed"
    rejected = "rejected"
    superseded = "superseded"  # replaced by a confirmed alternative
    cancelled = "cancelled"

class CompletionStatus(str, Enum):
    pending = "pending"
    completed = "completed"
    partial = "partial"
    skipped = "skipped"
