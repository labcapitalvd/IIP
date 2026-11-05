"""Add links.user_form_assignments

Revision ID: 7d3e1f4a9c32
Revises: 6c2d0e3f8b21
Create Date: 2026-10-20 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '7d3e1f4a9c32'
down_revision: Union[str, Sequence[str], None] = '6c2d0e3f8b21'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'user_form_assignments',
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('form_id', sa.Uuid(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['auth.users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['form_id'], ['forms.forms.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'form_id', name='uq_user_form_assignments_user_form'),
        schema='links',
    )


def downgrade() -> None:
    op.drop_table('user_form_assignments', schema='links')
