"""Linked loop questions: questions.source_question_id, answers_card_entry.parent_entry_id

Revision ID: 9f5a3b6c1e54
Revises: 8e4f2a5b0d43
Create Date: 2026-11-06 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '9f5a3b6c1e54'
down_revision: Union[str, Sequence[str], None] = '8e4f2a5b0d43'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'questions',
        sa.Column('source_question_id', postgresql.UUID(as_uuid=True), nullable=True),
        schema='forms',
    )
    op.create_foreign_key(
        'fk_questions_source_question_id', 'questions', 'questions',
        ['source_question_id'], ['id'],
        source_schema='forms', referent_schema='forms', ondelete='SET NULL',
    )
    op.add_column(
        'answers_card_entry',
        sa.Column('parent_entry_id', postgresql.UUID(as_uuid=True), nullable=True),
        schema='submissions',
    )
    op.create_foreign_key(
        'fk_answers_card_entry_parent_entry_id', 'answers_card_entry', 'answers_card_entry',
        ['parent_entry_id'], ['id'],
        source_schema='submissions', referent_schema='submissions', ondelete='CASCADE',
    )
    op.create_index(
        'idx_answers_card_entry_parent_entry_id', 'answers_card_entry', ['parent_entry_id'], schema='submissions'
    )


def downgrade() -> None:
    op.drop_index('idx_answers_card_entry_parent_entry_id', table_name='answers_card_entry', schema='submissions')
    op.drop_constraint('fk_answers_card_entry_parent_entry_id', 'answers_card_entry', schema='submissions', type_='foreignkey')
    op.drop_column('answers_card_entry', 'parent_entry_id', schema='submissions')
    op.drop_constraint('fk_questions_source_question_id', 'questions', schema='forms', type_='foreignkey')
    op.drop_column('questions', 'source_question_id', schema='forms')
