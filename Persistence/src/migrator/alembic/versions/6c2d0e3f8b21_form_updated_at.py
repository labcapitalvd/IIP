"""Add forms.forms.updated_at

Revision ID: 6c2d0e3f8b21
Revises: 5b1c9d2e7a10
Create Date: 2026-10-20 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '6c2d0e3f8b21'
down_revision: Union[str, Sequence[str], None] = '5b1c9d2e7a10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'forms',
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        schema='forms',
    )


def downgrade() -> None:
    op.drop_column('forms', 'updated_at', schema='forms')
