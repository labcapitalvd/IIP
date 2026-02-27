from shared_db import UnitOfWork
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories import (
    AnswerRepository,
    CardEntryRepository,
    FieldRepository,
    FormRepository,
    SubmissionRepository,
    UserSubmissionLinkRepository,
)


class SubmissionUoW(UnitOfWork):
    """
    Unit of Work for Submission Context.
    Handles user responses, linking answers to submissions.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.submissions = SubmissionRepository(session)
        self.answers = AnswerRepository(session)
        self.user_links = UserSubmissionLinkRepository(session)
        self.card_entries = CardEntryRepository(session)
        # Read-only access to form structure for validation during submission
        self.forms = FormRepository(session)
        self.fields = FieldRepository(session)
