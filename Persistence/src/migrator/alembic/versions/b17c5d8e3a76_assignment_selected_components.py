"""links.user_form_assignments.selected_component_ids

Revision ID: b17c5d8e3a76
Revises: a06b4c7d2f65
Create Date: 2026-11-09 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'b17c5d8e3a76'
down_revision: Union[str, Sequence[str], None] = 'a06b4c7d2f65'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'user_form_assignments',
        sa.Column('selected_component_ids', postgresql.ARRAY(sa.Uuid()), nullable=True),
        schema='links',
    )


def downgrade() -> None:
    op.drop_column('user_form_assignments', 'selected_component_ids', schema='links')
