"""forms.field_choice_text_inputs y submissions.answers_choice_texts

Revision ID: e40f8a1b6d09
Revises: d39e7f0a5c98
Create Date: 2026-11-20 12:46:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "e40f8a1b6d09"
down_revision: Union[str, Sequence[str], None] = "d39e7f0a5c98"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "field_choice_text_inputs",
        sa.Column("choice_id", sa.Uuid(), nullable=False),
        sa.Column(
            "is_required",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("placeholder", sa.String(length=255), nullable=True),
        sa.Column("max_length", sa.Integer(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["choice_id"], ["forms.field_choices.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "choice_id", name="uq_field_choice_text_inputs_choice_id"
        ),
        schema="forms",
    )

    op.create_table(
        "answers_choice_texts",
        sa.Column("answer_id", sa.Uuid(), nullable=False),
        sa.Column("choice_id", sa.Uuid(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["answer_id"], ["submissions.answers.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["choice_id"], ["forms.field_choices.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "answer_id", "choice_id", name="uq_answers_choice_texts_answer_choice"
        ),
        schema="submissions",
    )


def downgrade() -> None:
    op.drop_table("answers_choice_texts", schema="submissions")
    op.drop_table("field_choice_text_inputs", schema="forms")
