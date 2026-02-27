from shared_db import UnitOfWork
from ..repositories import (
    AnswerRepository,
    AnswerCardEntryRepository,
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

    submissions: SubmissionRepository
    answers: AnswerRepository
    user_links: UserSubmissionLinkRepository
    card_entries: AnswerCardEntryRepository
    forms: FormRepository
    fields: FieldRepository

    async def __aenter__(self):
        await super().__aenter__()
        assert self.session is not None

        self.submissions = SubmissionRepository(self.session)
        self.answers = AnswerRepository(self.session)
        self.user_links = UserSubmissionLinkRepository(self.session)
        self.card_entries = AnswerCardEntryRepository(self.session)
        # Read-only access to form structure for validation during submission
        self.forms = FormRepository(self.session)
        self.fields = FieldRepository(self.session)
        return self
