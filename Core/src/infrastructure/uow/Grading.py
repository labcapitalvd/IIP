from shared_db import UnitOfWork
from sqlalchemy.ext.asyncio import AsyncSession

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

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.grades = GradeRepository(session)
        self.results = ResultRepository(session)
        self.criteria = CriteriaRepository(session)
        # Read-only access to submissions
        self.submissions = SubmissionRepository(session)
