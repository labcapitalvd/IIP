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


def print_banner(
    text: str,
    border_char: str = "*",
    padding_x: int = 4,
    padding_y: int = 1,
    align: str = "center",
    width: int | None = None,
) -> None:
    """
    Prints a text block enclosed in a custom ASCII/Unicode border banner.

    :param text: The text string to print (can include newlines).
    :param border_char: Character used for the border (e.g., '*', '=', '─').
    :param padding_x: Horizontal spacing inside the box.
    :param padding_y: Vertical spacing (empty lines) inside the box.
    :param align: Text alignment ('left', 'center', 'right').
    :param width: Forced box width. If None, it auto-sizes to the longest line.
    """
    # Handle multi-line text by splitting into individual lines
    lines = text.splitlines() or [""]
    max_line_len = max(len(line) for line in lines)

    # Determine inner content width
    content_width = (
        max(max_line_len, width - (padding_x * 2)) if width else max_line_len
    )
    box_width = content_width + (padding_x * 2)

    border_line = border_char * (box_width + 2)  # +2 for the immediate side borders

    print()
    print(border_line)

    # Top vertical padding
    for _ in range(padding_y):
        print(f"{border_char}{' ' * box_width}{border_char}")

    # Content lines
    for line in lines:
        if align == "center":
            formatted_line = line.center(content_width)
        elif align == "right":
            formatted_line = line.rjust(content_width)
        else:  # left
            formatted_line = line.ljust(content_width)

        print(
            f"{border_char}{' ' * padding_x}{formatted_line}{' ' * padding_x}{border_char}"
        )

    # Bottom vertical padding
    for _ in range(padding_y):
        print(f"{border_char}{' ' * box_width}{border_char}")

    print(border_line)
    print()


def print_list(
    title: str,
    items: list[str],
    cols: int = 3,
    sort: bool = True,
    border_char: str = "─",
) -> None:
    """
    Prints a list of items formatted neatly into columns with borders.
    """
    if not items:
        print(f"\n{title}: (Empty)")
        return

    # Safely sort without risking mutation issues if a tuple/iterable is passed
    formatted_items = sorted(items) if sort else list(items)
    num_items = len(formatted_items)

    # Ensure columns don't exceed the number of items
    cols = max(1, min(cols, num_items))
    rows = math.ceil(num_items / cols)

    # Calculate required cell width
    item_width = max(len(str(item)) for item in formatted_items) + 4
    total_width = item_width * cols

    # Auto-adjust column count if it overflows the terminal width
    term_width = shutil.get_terminal_size((80, 24)).columns
    if total_width > term_width and cols > 1:
        # Fallback: recalculate cols based on available terminal width
        cols = max(1, term_width // item_width)
        rows = math.ceil(num_items / cols)
        total_width = item_width * cols

    print(f"\n{title} ({num_items}):")
    print(border_char * total_width)  # Top border

    for row in range(rows):
        line = ""
        for col in range(cols):
            # Column-first layout index calculation
            index = row + (col * rows)
            if index < num_items:
                line += f"{str(formatted_items[index]):<{item_width}}"
        print(line)

    print(border_char * total_width)  # Bottom border


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
