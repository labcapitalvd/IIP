from shared_db import UnitOfWork
from ..repositories import (
    AnswerRepository,
    AnswerBooleanRepository,
    AnswerCardEntryRepository,
    AnswerDateRepository,
    AnswerFileRepository,
    AnswerMultiChoiceRepository,
    AnswerNumericRepository,
    AnswerSingleChoiceRepository,
    AnswerTextRepository,
    FieldRepository,
    FormRepository,
    MultiChoiceOptionLinkRepository,
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
    answers_boolean: AnswerBooleanRepository
    answers_card_entry: AnswerCardEntryRepository
    answers_date: AnswerDateRepository
    answers_file: AnswerFileRepository
    answers_multi_choice: AnswerMultiChoiceRepository
    answers_numeric: AnswerNumericRepository
    answers_single_choice: AnswerSingleChoiceRepository
    answers_text: AnswerTextRepository

    user_links: UserSubmissionLinkRepository
    multichoice_links: MultiChoiceOptionLinkRepository

    forms: FormRepository
    fields: FieldRepository

    async def __aenter__(self):
        await super().__aenter__()
        assert self.session is not None

        self.submissions = SubmissionRepository(self.session)
        self.answers = AnswerRepository(self.session)
        self.answers_boolean = AnswerBooleanRepository(self.session)
        self.answers_card_entry = AnswerCardEntryRepository(self.session)
        self.answers_date = AnswerDateRepository(self.session)
        self.answers_file = AnswerFileRepository(self.session)
        self.answers_multi_choice = AnswerMultiChoiceRepository(self.session)
        self.answers_numeric = AnswerNumericRepository(self.session)
        self.answers_single_choice = AnswerSingleChoiceRepository(self.session)
        self.answers_text = AnswerTextRepository(self.session)

        self.user_links = UserSubmissionLinkRepository(self.session)
        self.multichoice_links = MultiChoiceOptionLinkRepository(self.session)

        # Read-only access to form structure for validation during submission
        self.forms = FormRepository(self.session)
        self.fields = FieldRepository(self.session)
        return self
