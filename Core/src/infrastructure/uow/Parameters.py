from shared.db import UnitOfWork


class ParametersUoW(UnitOfWork):
    """Unit of Work for generic parameter (lookup table) maintenance. Uses the session directly."""

    def _init_repositories(self) -> None:
        return None
