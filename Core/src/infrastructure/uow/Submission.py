from shared.db import UnitOfWork
from ..repositories import (
    AnswerRepository,
    FieldRepository,
    FormRepository,
    MultiChoiceOptionLinkRepository,
    SubmissionRepository,
    UserActorLinkRepository,
)


class SubmissionUoW(UnitOfWork):
    """
    Unit of Work for Submission Context.
    Handles user responses, linking answers to submissions.
    """

    submissions: SubmissionRepository
    answers: AnswerRepository

    user_actor_links: UserActorLinkRepository
    multichoice_links: MultiChoiceOptionLinkRepository

    forms: FormRepository
    fields: FieldRepository

    def _init_repositories(self) -> None:
        assert self.session is not None

        self.submissions = SubmissionRepository(self.session)
        self.answers = AnswerRepository(self.session)

        self.user_actor_links = UserActorLinkRepository(self.session)
        self.multichoice_links = MultiChoiceOptionLinkRepository(self.session)

        # Read-only access to form structure for validation during submission
        self.forms = FormRepository(self.session)
        self.fields = FieldRepository(self.session)
