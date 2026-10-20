"""Add forms.sections.icon

Revision ID: 5b1c9d2e7a10
Revises: 4af16f57b7da
Create Date: 2026-10-20 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '5b1c9d2e7a10'
down_revision: Union[str, Sequence[str], None] = '4af16f57b7da'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('sections', sa.Column('icon', sa.String(length=50), nullable=True), schema='forms')


def downgrade() -> None:
    op.drop_column('sections', 'icon', schema='forms')
