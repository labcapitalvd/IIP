import re
import unicodedata

import bleach
import emoji
from email_validator import EmailNotValidError, validate_email

from .errors import TextEmpty, TextMalformed

MAX_TEXT_LENGTH = 10_000
MAX_EMAIL_LENGTH = 254

CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
MULTISPACE_RE = re.compile(r"[ ]{2,}")


def _remove_emojis(text: str) -> str:
    """Replaces all emojis with an empty string"""
    return emoji.replace_emoji(text, replace="")


def _remove_html(text: str) -> str:
    """Completely strips all HTML tags and attributes"""
    return bleach.clean(text, tags=[], attributes={}, strip=True)


def _normalize_text(text: str) -> str:
    """Normalize text to NFKC"""

    return unicodedata.normalize("NFKC", text)


def sanitize_text(
    text: str,
    *,
    remove_emojis: bool = False,
    remove_html: bool = True,
) -> str:
    """Cleans up text from:
    - Control characters.
    - HTML
    - Emojis (optional)
    """

    if not text or not text.strip():
        raise TextEmpty("Sanitation target is empty.")

    if len(text) > MAX_TEXT_LENGTH:
        raise TextMalformed("Text too long.")

    text = _normalize_text(text)
    text = CONTROL_CHARS_RE.sub("", text)

    if remove_html:
        text = _remove_html(text)

    if remove_emojis:
        text = _remove_emojis(text)

    text = MULTISPACE_RE.sub(" ", text)
    text = text.strip()

    return text


def sanitize_email(email: str) -> str:
    """
    Final sanitization before DB persistence.
    Raises ValueError or TextMalformedTarget on failure.
    """
    if not email or not (email := email.strip()):
        raise ValueError("Email is empty.")

    email = _normalize_text(email)

    if len(email) > MAX_EMAIL_LENGTH:
        raise TextMalformed(f"Email exceeds DB limit of {MAX_EMAIL_LENGTH}")

    try:
        email_info = validate_email(email, check_deliverability=False)
        return email_info.normalized

    except EmailNotValidError as e:
        raise TextMalformed(f"Invalid email: {str(e)}")
