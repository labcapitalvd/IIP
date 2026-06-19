from shared.db import UnitOfWork
from ..repositories import (
    AnswerRepository,
    FieldRepository,
    FormRepository,
    MultiChoiceOptionLinkRepository,
    SubmissionRepository,
    UserActorLinkRepository,
    UserSubmissionLinkRepository,
)


class SubmissionUoW(UnitOfWork):
    """
    Unit of Work for Submission Context.
    Handles user responses, linking answers to submissions.
    """

    submissions: SubmissionRepository
    answers: AnswerRepository

    user_submission_links: UserSubmissionLinkRepository
    user_actor_links: UserActorLinkRepository
    multichoice_links: MultiChoiceOptionLinkRepository

    forms: FormRepository
    fields: FieldRepository

    async def __aenter__(self):
        await super().__aenter__()
        assert self.session is not None

        self.submissions = SubmissionRepository(self.session)
        self.answers = AnswerRepository(self.session)

        self.user_submission_links = UserSubmissionLinkRepository(self.session)
        self.user_actor_links = UserActorLinkRepository(self.session)
        self.multichoice_links = MultiChoiceOptionLinkRepository(self.session)

        # Read-only access to form structure for validation during submission
        self.forms = FormRepository(self.session)
        self.fields = FieldRepository(self.session)
        return self
