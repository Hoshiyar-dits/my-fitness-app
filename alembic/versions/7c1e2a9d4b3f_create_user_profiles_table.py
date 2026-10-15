"""create user_profiles table

Revision ID: 7c1e2a9d4b3f
Revises: 488bf7748bbd
Create Date: 2026-10-15 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7c1e2a9d4b3f'
down_revision: Union[str, Sequence[str], None] = '488bf7748bbd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('user_profiles',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('date_of_birth', sa.Date(), nullable=False),
    sa.Column('height_cm', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('gender', sa.String(length=30), nullable=True),
    sa.Column('activity_level', sa.String(length=30), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('user_profiles')
