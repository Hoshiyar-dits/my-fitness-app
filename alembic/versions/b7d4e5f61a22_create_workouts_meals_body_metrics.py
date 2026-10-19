"""create workouts, meals and body_metrics tables

Revision ID: b7d4e5f61a22
Revises: a3f8c21d9e10
Create Date: 2026-10-16 10:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7d4e5f61a22'
down_revision: Union[str, Sequence[str], None] = 'a3f8c21d9e10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('workouts',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('workout_date', sa.Date(), nullable=False),
    sa.Column('workout_type', sa.String(length=30), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('duration_minutes', sa.Integer(), nullable=False),
    sa.Column('calories_burned', sa.Integer(), nullable=True),
    sa.Column('intensity', sa.String(length=20), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_workouts_user_date', 'workouts', ['user_id', 'workout_date'])

    op.create_table('meals',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('meal_date', sa.Date(), nullable=False),
    sa.Column('meal_type', sa.String(length=20), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('calories', sa.Integer(), nullable=False),
    sa.Column('protein_g', sa.Numeric(precision=6, scale=2), nullable=True),
    sa.Column('carbs_g', sa.Numeric(precision=6, scale=2), nullable=True),
    sa.Column('fat_g', sa.Numeric(precision=6, scale=2), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_meals_user_date', 'meals', ['user_id', 'meal_date'])

    op.create_table('body_metrics',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('log_date', sa.Date(), nullable=False),
    sa.Column('weight_kg', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('body_fat_pct', sa.Numeric(precision=4, scale=1), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'log_date', name='uq_body_metrics_user_date')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('body_metrics')
    op.drop_table('meals')
    op.drop_table('workouts')
