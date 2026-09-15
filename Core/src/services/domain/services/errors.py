from shared.utils import BaseDomainError


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


class FormError(BaseDomainError):
    """Base error for Form design domain logic."""

    status_code = 400
    message = "An error occurred in the Form design service."


class FormAlreadyExistsError(FormError):
    status_code = 409  # Conflict
    message = "A form with this code is already registered in the system."


class FormNotFoundError(FormError):
    status_code = 404  # Not Found
    message = "The specified form could not be found."


class FieldTypeNotFoundError(FormError):
    status_code = 404  # Not Found
    message = "The specified field type could not be found."


class SectionTypeNotFoundError(FormError):
    status_code = 404  # Not Found
    message = "The specified section type could not be found."


class FormStructureConflictError(FormError):
    status_code = 409  # Conflict
    message = "Duplicate codes were found within the submitted form structure."
