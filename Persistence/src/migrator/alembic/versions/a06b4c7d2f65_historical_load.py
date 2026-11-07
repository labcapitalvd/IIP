"""Historical load: forms.edition_closed_at, grading.form_results, grading.section_results

Revision ID: a06b4c7d2f65
Revises: 9f5a3b6c1e54
Create Date: 2026-11-06 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'a06b4c7d2f65'
down_revision: Union[str, Sequence[str], None] = '9f5a3b6c1e54'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'forms',
        sa.Column('edition_closed_at', sa.DateTime(timezone=True), nullable=True),
        schema='forms',
    )
    op.create_table(
        'form_results',
        sa.Column('form_id', sa.Uuid(), nullable=False),
        sa.Column('actor_id', sa.Uuid(), nullable=False),
        sa.Column('total', sa.Numeric(14, 4), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.ForeignKeyConstraint(['form_id'], ['forms.forms.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['actor_id'], ['actors.actors.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('form_id', 'actor_id', name='uq_form_results_form_actor'),
        schema='grading',
    )
    op.create_table(
        'section_results',
        sa.Column('form_result_id', sa.Uuid(), nullable=False),
        sa.Column('section_id', sa.Uuid(), nullable=False),
        sa.Column('score', sa.Numeric(14, 4), nullable=True),
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.ForeignKeyConstraint(['form_result_id'], ['grading.form_results.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['section_id'], ['forms.sections.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('form_result_id', 'section_id', name='uq_section_results_result_section'),
        schema='grading',
    )


def downgrade() -> None:
    op.drop_table('section_results', schema='grading')
    op.drop_table('form_results', schema='grading')
    op.drop_column('forms', 'edition_closed_at', schema='forms')
