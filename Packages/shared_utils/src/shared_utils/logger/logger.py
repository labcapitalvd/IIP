import os
import sys
import logging
from typing import Literal


LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

_LOG_LEVELS: dict[str, int] = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def _get_log_level() -> int:
    # getLevelName can take a string like "DEBUG" and return 10
    level_name = os.environ.get("LOGLEVEL", "INFO").upper()
    return logging.getLevelNamesMapping().get(level_name, logging.INFO)


def configure_logging() -> None:
    logging.basicConfig(
        level=_get_log_level(),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
