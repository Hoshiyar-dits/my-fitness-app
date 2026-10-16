"""add password to users

Revision ID: a3f8c21d9e10
Revises: 7c1e2a9d4b3f
Create Date: 2026-10-16 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3f8c21d9e10'
down_revision: Union[str, Sequence[str], None] = '7c1e2a9d4b3f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('password', sa.String(length=255), nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'password')
