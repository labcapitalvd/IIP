from shared_utils import BaseDomainError


class ActorError(BaseDomainError):
    """Base error for Actor domain logic."""

    status_code = 400
    message = "An error occurred in the Actor service."


class ActorSegmentError(BaseDomainError):
    """Base error for Actor domain logic."""

    status_code = 400
    message = "An error occurred in the Actor Segment service."


class ActorAlreadyExistsError(ActorError):
    status_code = 409  # Conflict is more accurate for "already exists"
    message = "This actor is already registered in the system."


class ActorSegmentAlreadyExistsError(ActorSegmentError):
    status_code = 409  # Conflict is more accurate for "already exists"
    message = "This actor is already registered in the system."


class ActorNotFoundError(ActorError):
    status_code = 404  # Not Found
    message = "The specified actor could not be found."


class ActorSegmentNotFoundError(ActorSegmentError):
    status_code = 404  # Not Found
    message = "The specified segment could not be found."
