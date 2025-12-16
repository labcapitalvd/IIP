"""Poblado de questions desde hierarchy.json"""
import os
import logging


LOGLEVEL = os.environ["LOGLEVEL"].lower() in (
    "debug",
    "info",
    "warning",
    "error",
    "critical",
)

logger = logging.getLogger("SeedQuestions")
logger.setLevel(LOGLEVEL)

def upgrade() -> None:
    pass