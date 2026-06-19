import re
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from shared.utils.logger import get_logger


logger = get_logger(__name__)


class BaseDomainError(Exception):
    status_code = 400
    message = "An error occurred"

    def __init__(self, message=None):
        self.message = message or self.message
        super().__init__(self.message)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "code": "VALIDATION_ERROR",
            "message": "Invalid input data",
            "detail": exc.errors(),
        },
    )


async def domain_exception_handler(request: Request, exc: BaseDomainError):
    """
    Global handler for all business logic errors.
    Automatically picks up status_code and message from your classes.
    """
    raw_name = type(exc).__name__
    snake_case_name = re.sub(r"(?<!^)(?=[A-Z])", "_", raw_name).upper()
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "code": snake_case_name,
            "message": exc.message,
            "detail": None,
        },
    )


async def universal_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
            "detail": None,
        },
    )
