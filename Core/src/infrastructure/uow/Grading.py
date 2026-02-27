from shared_db import UnitOfWork
from ..repositories import (
    CriteriaRepository,
    GradeRepository,
    ResultRepository,
    SubmissionRepository,
)


class GradingUoW(UnitOfWork):
    """
    Unit of Work for Grading/Evaluation Context.
    Handles scoring, results calculation, and criteria management.
    """

    grades: GradeRepository
    results: ResultRepository
    criteria: CriteriaRepository
    submissions: SubmissionRepository

    async def __aenter__(self):
        await super().__aenter__()
        assert self.session is not None

        self.grades = GradeRepository(self.session)
        self.results = ResultRepository(self.session)
        self.criteria = CriteriaRepository(self.session)
        # Read-only access to submissions
        self.submissions = SubmissionRepository(self.session)
        return self
