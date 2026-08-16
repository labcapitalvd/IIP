import re
import unicodedata

import shutil
import bleach
import emoji
import math
from email_validator import EmailNotValidError, validate_email

from .errors import TextEmpty, TextMalformed

MAX_TEXT_LENGTH = 10_000
MAX_EMAIL_LENGTH = 254

CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
MULTISPACE_RE = re.compile(r"[ ]{2,}")


def format_banner(
    text: str,
    border_h: str = "─",
    border_v: str | None = "|",
    corner: str | None = "*",
    padding_x: int = 4,
    padding_y: int = 1,
    align: str = "center",
    width: int | None = None,
) -> str:
    """Formats a text block inside a custom ASCII/Unicode border banner."""
    border_v = border_v if border_v is not None else border_h
    corner = corner if corner is not None else border_v

    lines = text.strip().splitlines() or [""]
    max_line_len = max(len(line) for line in lines)

    content_width = (
        max(max_line_len, width - (padding_x * 2)) if width else max_line_len
    )
    box_width = content_width + (padding_x * 2)

    border_line = f"{corner}{border_h * box_width}{corner}"
    padding_row = f"{border_v}{' ' * box_width}{border_v}"

    output = [border_line]

    # Top padding
    output.extend([padding_row] * padding_y)

    # Content lines
    for line in lines:
        if align == "center":
            formatted_line = line.center(content_width)
        elif align == "right":
            formatted_line = line.rjust(content_width)
        else:
            formatted_line = line.ljust(content_width)

        output.append(
            f"{border_v}{' ' * padding_x}{formatted_line}{' ' * padding_x}{border_v}"
        )

    # Bottom padding
    output.extend([padding_row] * padding_y)
    output.append(border_line)

    return f"\n{'\n'.join(output)}\n"


def format_list(
    title: str,
    items: list[str],
    cols: int = 3,
    sort: bool = True,
    border_h: str = "─",
    border_v: str | None = "|",
    corner: str | None = "*",
    padding_x: int = 2,
    border_char: str | None = None,
) -> str:
    """Formats a list of items into an aligned grid enclosed in a boxed border."""
    # Maintain backwards-compatibility if border_char is passed
    if border_char is not None:
        border_h = border_char

    border_v = border_v if border_v is not None else border_h
    corner = corner if corner is not None else border_v

    if not items:
        return f"\n{title}: (Empty)\n"

    formatted_items = sorted(items) if sort else list(items)
    num_items = len(formatted_items)

    cols = max(1, min(cols, num_items))
    rows = math.ceil(num_items / cols)

    item_width = max(len(str(item)) for item in formatted_items) + 4
    grid_width = item_width * cols
    header_text = f"{title} ({num_items}):"

    # Auto-adjust column count for terminal width
    term_width = shutil.get_terminal_size((80, 24)).columns
    max_content_width = max(10, term_width - (padding_x * 2) - 2)

    if grid_width > max_content_width and cols > 1:
        cols = max(1, max_content_width // item_width)
        rows = math.ceil(num_items / cols)
        grid_width = item_width * cols

    content_width = max(grid_width, len(header_text))
    box_width = content_width + (padding_x * 2)

    border_line = f"{corner}{border_h * box_width}{corner}"
    divider_line = f"{border_v}{border_h * box_width}{border_v}"

    lines = [border_line]

    # Title Header Row (fixed format specifier)
    lines.append(
        f"{border_v}{' ' * padding_x}{header_text:<{content_width}}{' ' * padding_x}{border_v}"
    )
    lines.append(divider_line)

    # Grid Content Rows (fixed format specifier)
    for row in range(rows):
        line = ""
        for col in range(cols):
            index = row + (col * rows)
            if index < num_items:
                line += f"{str(formatted_items[index]):<{item_width}}"

        lines.append(
            f"{border_v}{' ' * padding_x}{line:<{content_width}}{' ' * padding_x}{border_v}"
        )

    lines.append(border_line)

    return f"\n{'\n'.join(lines)}\n"


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
