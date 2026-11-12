"""grading.question_results: puntaje histórico por pregunta

Revision ID: d39e7f0a5c98
Revises: c28d6e9f4b87
Create Date: 2026-11-12 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'd39e7f0a5c98'
down_revision: Union[str, Sequence[str], None] = 'c28d6e9f4b87'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'question_results',
        sa.Column('form_result_id', sa.Uuid(), nullable=False),
        sa.Column('question_id', sa.Uuid(), nullable=False),
        sa.Column('score', sa.Numeric(14, 4), nullable=True),
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.ForeignKeyConstraint(['form_result_id'], ['grading.form_results.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['question_id'], ['forms.questions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('form_result_id', 'question_id', name='uq_question_results_result_question'),
        schema='grading',
    )


def downgrade() -> None:
    op.drop_table('question_results', schema='grading')
