"""add 25-day training program tables

Adds goals, exercise catalog, training programs, planned/performed exercises, daily check-ins,
performance activities with splits and daily analyses. Extends meals (time, accuracy, source) and
body_metrics (body fat method). Additive only: no existing column or row is changed or dropped.

Revision ID: d4e8f2a1b6c7
Revises: c91a0b7e3d55
Create Date: 2026-10-19 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e8f2a1b6c7'
down_revision: Union[str, Sequence[str], None] = 'c91a0b7e3d55'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# copy of app/training/exercise_catalog.py at the time of this migration
EXERCISES = [
        {'name': 'Dynamic warm-up', 'category': 'warm_up', 'is_high_impact': False, 'required_equipment': None, 'description': '5 min easy jog, then leg swings, high knees, butt kicks and skips.'},
        {'name': 'A-skips', 'category': 'sprint', 'is_high_impact': False, 'required_equipment': None, 'description': 'Rhythmic skipping drill focusing on knee lift and foot strike under the hips.'},
        {'name': 'Strides', 'category': 'sprint', 'is_high_impact': False, 'required_equipment': None, 'description': 'Relaxed, gradually faster runs at 70-80% effort with full walk-back recovery.'},
        {'name': 'Acceleration sprints', 'category': 'sprint', 'is_high_impact': True, 'required_equipment': None, 'description': 'Short sprints from a standing start focusing on forward lean and powerful pushes.'},
        {'name': 'Flying sprints', 'category': 'sprint', 'is_high_impact': True, 'required_equipment': None, 'description': 'Build up over 20 m, then hold near-top speed through a short zone.'},
        {'name': 'Easy run', 'category': 'endurance', 'is_high_impact': False, 'required_equipment': None, 'description': 'Conversational pace - you can speak in full sentences. Walk breaks are fine.'},
        {'name': 'Tempo run', 'category': 'endurance', 'is_high_impact': False, 'required_equipment': None, 'description': 'Comfortably hard, steady pace you could hold for about an hour when fresh.'},
        {'name': 'Run intervals', 'category': 'endurance', 'is_high_impact': False, 'required_equipment': None, 'description': 'Repeated faster efforts with easy jog recovery between them.'},
        {'name': 'Pop-up jumps', 'category': 'long_jump', 'is_high_impact': True, 'required_equipment': None, 'description': 'Short approach, single-leg take-off, drive the knee up and land on both feet.'},
        {'name': 'Standing long jump', 'category': 'long_jump', 'is_high_impact': True, 'required_equipment': None, 'description': 'Two-foot take-off and landing. Swing arms, extend hips, land softly.'},
        {'name': 'Bounding', 'category': 'long_jump', 'is_high_impact': True, 'required_equipment': None, 'description': 'Exaggerated running strides with long ground contact and high knee drive.'},
        {'name': 'High jump approach curve runs', 'category': 'high_jump', 'is_high_impact': False, 'required_equipment': None, 'description': 'Run the J-shaped approach without jumping to rehearse rhythm and lean.'},
        {'name': 'High jump take-off drill', 'category': 'high_jump', 'is_high_impact': True, 'required_equipment': None, 'description': 'Curve approach of 3-5 steps into a vertical single-leg take-off, no bar.'},
        {'name': 'Scissor jumps', 'category': 'high_jump', 'is_high_impact': True, 'required_equipment': 'high_jump_setup', 'description': 'Short approach scissor jump over a low bar or elastic onto a mat.'},
        {'name': 'Fosbury flop technique jumps', 'category': 'high_jump', 'is_high_impact': True, 'required_equipment': 'high_jump_setup', 'description': 'Short-approach flop over a low bar onto a proper landing mat.'},
        {'name': 'Bodyweight squat', 'category': 'strength', 'is_high_impact': False, 'required_equipment': None, 'description': 'Controlled squat to a comfortable depth.'},
        {'name': 'Goblet squat', 'category': 'strength', 'is_high_impact': False, 'required_equipment': 'dumbbells', 'description': 'Squat holding a dumbbell or kettlebell at the chest.'},
        {'name': 'Romanian deadlift', 'category': 'strength', 'is_high_impact': False, 'required_equipment': 'dumbbells', 'description': 'Hip hinge with dumbbells or a barbell, slight knee bend, neutral back.'},
        {'name': 'Glute bridge', 'category': 'strength', 'is_high_impact': False, 'required_equipment': None, 'description': 'Lying on your back, drive hips up by squeezing the glutes.'},
        {'name': 'Split squat', 'category': 'strength', 'is_high_impact': False, 'required_equipment': None, 'description': 'Static lunge position, lower the back knee towards the floor. Reps per leg.'},
        {'name': 'Calf raises', 'category': 'strength', 'is_high_impact': False, 'required_equipment': None, 'description': 'Slow raises onto the toes, pause at the top, lower under control.'},
        {'name': 'Plank', 'category': 'strength', 'is_high_impact': False, 'required_equipment': None, 'description': 'Forearm plank with a straight line from head to heels.'},
        {'name': 'Hip mobility flow', 'category': 'mobility', 'is_high_impact': False, 'required_equipment': None, 'description': "Hip circles, 90/90 switches, hip-flexor stretch and world's greatest stretch."},
        {'name': 'Ankle and calf mobility', 'category': 'mobility', 'is_high_impact': False, 'required_equipment': None, 'description': 'Knee-to-wall ankle mobilisations and gentle calf stretches.'},
        {'name': 'Easy walk', 'category': 'recovery', 'is_high_impact': False, 'required_equipment': None, 'description': 'Relaxed walk at an easy pace.'},
        {'name': 'Sprint assessment', 'category': 'assessment', 'is_high_impact': True, 'required_equipment': None, 'description': 'Timed sprint from a standing start. Same distance, surface and timing method every time.'},
        {'name': 'Long jump assessment', 'category': 'assessment', 'is_high_impact': True, 'required_equipment': None, 'description': 'Measured standing long jump: take-off line to the back-most landing mark.'},
        {'name': 'High jump assessment', 'category': 'assessment', 'is_high_impact': True, 'required_equipment': 'high_jump_setup', 'description': 'Measured bar clearance with a short approach and increasing heights.'},
        {'name': 'Run assessment', 'category': 'assessment', 'is_high_impact': False, 'required_equipment': None, 'description': 'Timed run over the assessment distance on the same route/surface every time.'}
]


def _timestamps():
    return [
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    ]


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('meals', sa.Column('meal_time', sa.Time(), nullable=True))
    op.add_column('meals', sa.Column('nutrition_accuracy', sa.String(length=20), server_default='estimated', nullable=False))
    op.add_column('meals', sa.Column('nutrition_source', sa.String(length=100), nullable=True))
    op.add_column('body_metrics', sa.Column('body_fat_method', sa.String(length=30), nullable=True))

    exercises = op.create_table('exercises',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('category', sa.String(length=30), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('is_high_impact', sa.Boolean(), nullable=False),
    sa.Column('required_equipment', sa.String(length=50), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.bulk_insert(exercises, EXERCISES)

    op.create_table('training_programs',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('start_date', sa.Date(), nullable=False),
    sa.Column('end_date', sa.Date(), nullable=False),
    sa.Column('status', sa.String(length=30), nullable=False),
    sa.Column('experience_level', sa.String(length=20), nullable=False),
    sa.Column('training_background', sa.Text(), nullable=True),
    sa.Column('available_minutes_per_day', sa.SmallInteger(), nullable=False),
    sa.Column('equipment', sa.JSON(), nullable=False),
    sa.Column('injury_history', sa.Text(), nullable=True),
    sa.Column('current_pain', sa.Text(), nullable=True),
    sa.Column('medical_restrictions', sa.Text(), nullable=True),
    sa.Column('medical_clearance_confirmed', sa.Boolean(), nullable=False),
    sa.Column('assessment_run_distance_m', sa.Numeric(precision=9, scale=2), nullable=False),
    sa.Column('assessment_sprint_distance_m', sa.Numeric(precision=6, scale=2), nullable=False),
    sa.Column('notes', sa.Text(), nullable=True),
    *_timestamps(),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_training_programs_user_status', 'training_programs', ['user_id', 'status'])

    op.create_table('fitness_goals',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('program_id', sa.BigInteger(), nullable=True),
    sa.Column('goal_type', sa.String(length=30), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=True),
    sa.Column('unit', sa.String(length=10), nullable=False),
    sa.Column('reference_distance_m', sa.Numeric(precision=9, scale=2), nullable=True),
    sa.Column('technique', sa.String(length=30), nullable=True),
    sa.Column('start_date', sa.Date(), nullable=False),
    sa.Column('target_date', sa.Date(), nullable=False),
    sa.Column('baseline_value', sa.Numeric(precision=10, scale=3), nullable=True),
    sa.Column('target_value', sa.Numeric(precision=10, scale=3), nullable=False),
    sa.Column('current_value', sa.Numeric(precision=10, scale=3), nullable=True),
    sa.Column('current_value_date', sa.Date(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    *_timestamps(),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['program_id'], ['training_programs.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_fitness_goals_user_status', 'fitness_goals', ['user_id', 'status'])

    op.create_table('planned_workouts',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('program_id', sa.BigInteger(), nullable=True),
    sa.Column('plan_date', sa.Date(), nullable=False),
    sa.Column('day_number', sa.SmallInteger(), nullable=True),
    sa.Column('training_phase', sa.String(length=30), nullable=True),
    sa.Column('session_type', sa.String(length=30), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('warm_up', sa.Text(), nullable=True),
    sa.Column('cool_down', sa.Text(), nullable=True),
    sa.Column('intensity', sa.String(length=20), nullable=False),
    sa.Column('estimated_duration_minutes', sa.SmallInteger(), nullable=False),
    sa.Column('is_high_impact', sa.Boolean(), nullable=False),
    sa.Column('source', sa.String(length=20), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('confirmed_at', sa.DateTime(), nullable=True),
    sa.Column('adjustment_reason', sa.Text(), nullable=True),
    sa.Column('based_on_plan_id', sa.BigInteger(), nullable=True),
    sa.Column('completion_status', sa.String(length=20), nullable=False),
    sa.Column('skip_reason', sa.Text(), nullable=True),
    sa.Column('actual_duration_minutes', sa.SmallInteger(), nullable=True),
    sa.Column('perceived_effort', sa.SmallInteger(), nullable=True),
    sa.Column('completion_notes', sa.Text(), nullable=True),
    sa.Column('completed_at', sa.DateTime(), nullable=True),
    sa.Column('workout_id', sa.BigInteger(), nullable=True),
    *_timestamps(),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['program_id'], ['training_programs.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['based_on_plan_id'], ['planned_workouts.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['workout_id'], ['workouts.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_planned_workouts_user_date', 'planned_workouts', ['user_id', 'plan_date'])

    op.create_table('planned_exercises',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('planned_workout_id', sa.BigInteger(), nullable=False),
    sa.Column('exercise_id', sa.Integer(), nullable=False),
    sa.Column('position', sa.SmallInteger(), nullable=False),
    sa.Column('sets', sa.SmallInteger(), nullable=True),
    sa.Column('reps', sa.SmallInteger(), nullable=True),
    sa.Column('distance_m', sa.Numeric(precision=9, scale=2), nullable=True),
    sa.Column('duration_seconds', sa.Integer(), nullable=True),
    sa.Column('rest_seconds', sa.Integer(), nullable=True),
    sa.Column('effort', sa.String(length=100), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['planned_workout_id'], ['planned_workouts.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['exercise_id'], ['exercises.id']),
    sa.PrimaryKeyConstraint('id')
    )

    op.create_table('performed_exercises',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('planned_workout_id', sa.BigInteger(), nullable=False),
    sa.Column('exercise_id', sa.Integer(), nullable=False),
    sa.Column('sets', sa.SmallInteger(), nullable=True),
    sa.Column('reps', sa.SmallInteger(), nullable=True),
    sa.Column('distance_m', sa.Numeric(precision=9, scale=2), nullable=True),
    sa.Column('duration_seconds', sa.Integer(), nullable=True),
    sa.Column('load_kg', sa.Numeric(precision=6, scale=2), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['planned_workout_id'], ['planned_workouts.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['exercise_id'], ['exercises.id']),
    sa.PrimaryKeyConstraint('id')
    )

    op.create_table('daily_checkins',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('checkin_date', sa.Date(), nullable=False),
    sa.Column('sleep_hours', sa.Numeric(precision=3, scale=1), nullable=True),
    sa.Column('sleep_quality', sa.SmallInteger(), nullable=True),
    sa.Column('energy_level', sa.SmallInteger(), nullable=True),
    sa.Column('fatigue_level', sa.SmallInteger(), nullable=True),
    sa.Column('soreness_level', sa.SmallInteger(), nullable=True),
    sa.Column('pain_level', sa.SmallInteger(), nullable=True),
    sa.Column('pain_location', sa.String(length=255), nullable=True),
    sa.Column('warning_symptoms', sa.JSON(), nullable=False),
    sa.Column('workout_completed', sa.Boolean(), nullable=True),
    sa.Column('perceived_effort', sa.SmallInteger(), nullable=True),
    sa.Column('resting_heart_rate', sa.SmallInteger(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    *_timestamps(),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'checkin_date', name='uq_daily_checkins_user_date')
    )

    op.create_table('performance_activities',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('planned_workout_id', sa.BigInteger(), nullable=True),
    sa.Column('activity_date', sa.Date(), nullable=False),
    sa.Column('activity_type', sa.String(length=20), nullable=False),
    sa.Column('distance_m', sa.Numeric(precision=9, scale=2), nullable=True),
    sa.Column('elapsed_seconds', sa.Numeric(precision=9, scale=2), nullable=True),
    sa.Column('jump_cm', sa.Numeric(precision=6, scale=1), nullable=True),
    sa.Column('technique', sa.String(length=30), nullable=True),
    sa.Column('attempt_number', sa.SmallInteger(), nullable=True),
    sa.Column('is_assessment', sa.Boolean(), nullable=False),
    sa.Column('measurement_method', sa.String(length=30), nullable=True),
    sa.Column('conditions', sa.String(length=255), nullable=True),
    sa.Column('perceived_effort', sa.SmallInteger(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    *_timestamps(),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['planned_workout_id'], ['planned_workouts.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_performance_activities_user_type_date', 'performance_activities', ['user_id', 'activity_type', 'activity_date'])

    op.create_table('activity_splits',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('activity_id', sa.BigInteger(), nullable=False),
    sa.Column('split_number', sa.SmallInteger(), nullable=False),
    sa.Column('distance_m', sa.Numeric(precision=9, scale=2), nullable=False),
    sa.Column('elapsed_seconds', sa.Numeric(precision=9, scale=2), nullable=False),
    sa.ForeignKeyConstraint(['activity_id'], ['performance_activities.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('activity_id', 'split_number', name='uq_activity_splits_activity_number')
    )

    op.create_table('daily_analyses',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('program_id', sa.BigInteger(), nullable=True),
    sa.Column('analysis_date', sa.Date(), nullable=False),
    sa.Column('readiness', sa.String(length=30), nullable=False),
    sa.Column('summary', sa.Text(), nullable=False),
    sa.Column('reasons', sa.JSON(), nullable=False),
    sa.Column('metrics', sa.JSON(), nullable=False),
    sa.Column('source_refs', sa.JSON(), nullable=False),
    sa.Column('recommendation', sa.Text(), nullable=True),
    sa.Column('safety_message', sa.Text(), nullable=True),
    sa.Column('generated_by', sa.String(length=20), nullable=False),
    sa.Column('proposed_plan_id', sa.BigInteger(), nullable=True),
    *_timestamps(),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['program_id'], ['training_programs.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['proposed_plan_id'], ['planned_workouts.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'analysis_date', name='uq_daily_analyses_user_date')
    )


def downgrade() -> None:
    """Downgrade schema. WARNING: deletes all program, goal, check-in, activity and analysis data."""
    op.drop_table('daily_analyses')
    op.drop_table('activity_splits')
    op.drop_table('performance_activities')
    op.drop_table('daily_checkins')
    op.drop_table('performed_exercises')
    op.drop_table('planned_exercises')
    op.drop_table('planned_workouts')
    op.drop_table('fitness_goals')
    op.drop_table('training_programs')
    op.drop_table('exercises')
    op.drop_column('body_metrics', 'body_fat_method')
    op.drop_column('meals', 'nutrition_source')
    op.drop_column('meals', 'nutrition_accuracy')
    op.drop_column('meals', 'meal_time')
