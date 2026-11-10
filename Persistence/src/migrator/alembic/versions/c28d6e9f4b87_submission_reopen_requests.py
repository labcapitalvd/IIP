"""submissions.reopen_requests

Revision ID: c28d6e9f4b87
Revises: b17c5d8e3a76
Create Date: 2026-11-09 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'c28d6e9f4b87'
down_revision: Union[str, Sequence[str], None] = 'b17c5d8e3a76'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'reopen_requests',
        sa.Column('actor_id', sa.Uuid(), nullable=False),
        sa.Column('form_id', sa.Uuid(), nullable=False),
        sa.Column('requested_by_id', sa.Uuid(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('requested_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('resolved_by_id', sa.Uuid(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolution_note', sa.Text(), nullable=True),
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.ForeignKeyConstraint(['actor_id'], ['actors.actors.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['form_id'], ['forms.forms.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['requested_by_id'], ['auth.users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['resolved_by_id'], ['auth.users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        schema='submissions',
    )
    op.create_index('idx_reopen_requests_actor_form', 'reopen_requests', ['actor_id', 'form_id'], schema='submissions')


def downgrade() -> None:
    op.drop_index('idx_reopen_requests_actor_form', table_name='reopen_requests', schema='submissions')
    op.drop_table('reopen_requests', schema='submissions')
