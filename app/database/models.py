# ruff: noqa: F401 - imported only to register every model on Base.metadata (Alembic autogenerate, tests)
from app.users.models.user import User
from app.users.models.user_profiles import UserProfile
from app.workouts.models.workout import Workout
from app.meals.models.meal import Meal
from app.body_metrics.models.body_metric import BodyMetric
from app.chat.models.chat_message import ChatMessage
from app.training.models.training import Exercise, TrainingProgram, PlannedWorkout, PlannedExercise, PerformedExercise
from app.goals.models.fitness_goal import FitnessGoal
from app.checkins.models.daily_checkin import DailyCheckin
from app.activities.models.performance_activity import PerformanceActivity, ActivitySplit
from app.analysis.models.daily_analysis import DailyAnalysis
