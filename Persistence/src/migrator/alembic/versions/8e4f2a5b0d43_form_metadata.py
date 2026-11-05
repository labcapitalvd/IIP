"""Add forms.forms.year, version, is_active

Revision ID: 8e4f2a5b0d43
Revises: 7d3e1f4a9c32
Create Date: 2026-11-05 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '8e4f2a5b0d43'
down_revision: Union[str, Sequence[str], None] = '7d3e1f4a9c32'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('forms', sa.Column('year', sa.Integer(), nullable=True), schema='forms')
    op.add_column('forms', sa.Column('version', sa.String(length=20), nullable=True), schema='forms')
    op.add_column(
        'forms',
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        schema='forms',
    )
    # Formularios existentes cuyo código es un año (p. ej. '2027'): esa es su vigencia.
    op.execute("UPDATE forms.forms SET year = code::integer WHERE code ~ '^[0-9]{4}$'")


def downgrade() -> None:
    op.drop_column('forms', 'is_active', schema='forms')
    op.drop_column('forms', 'version', schema='forms')
    op.drop_column('forms', 'year', schema='forms')
