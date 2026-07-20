from shared.db import UnitOfWork
from ..repositories import (
    CriterionRepository,
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
    criteria: CriterionRepository
    submissions: SubmissionRepository

    def _init_repositories(self) -> None:
        assert self.session is not None

        self.grades = GradeRepository(self.session)
        self.results = ResultRepository(self.session)
        self.criteria = CriterionRepository(self.session)
        # Read-only access to submissions
        self.submissions = SubmissionRepository(self.session)
