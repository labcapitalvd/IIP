from shared.utils.seeding import is_uuidv7
from .encryption import encrypt, decrypt
from .error_handling import (
    BaseDomainError,
    domain_exception_handler,
    universal_exception_handler,
)
from .files import save_file, rename_file, delete_file
from .hashing import hash_string, hash_password, hash_token
from .hashing import verify_string, verify_password, verify_token
from .texts import sanitize_text, sanitize_email, format_list, format_banner
from .tokens import AccessContext, SessionContext
from .tokens import generate_token, decode_token, get_claims
from .logger import configure_logging, get_logger

from .seeding import (
    new_uuidv7,
    is_uuidv7,
    get_table_columns,
    validate_required_columns,
    clean_text,
    fold_for_comparison,
    assert_no_missing,
    assert_all_uuidv7,
    assert_no_duplicates,
)

__all__ = [
    "encrypt",
    "decrypt",
    "BaseDomainError",
    "domain_exception_handler",
    "universal_exception_handler",
    "save_file",
    "rename_file",
    "delete_file",
    "hash_password",
    "hash_token",
    "hash_string",
    "verify_password",
    "verify_token",
    "verify_string",
    "hash_text",
    "sanitize_text",
    "sanitize_email",
    "format_list",
    "format_banner",
    "AccessContext",
    "SessionContext",
    "generate_token",
    "decode_token",
    "get_claims",
    "configure_logging",
    "get_logger",
    # Assertions
    "assert_no_missing",
    "assert_all_uuidv7",
    "assert_no_duplicates",
    # Identifiers
    "new_uuidv7",
    "is_uuidv7",
    # Introspection
    "get_table_columns",
    "validate_required_columns",
    "assert_field_lengths",
    # Input / Output File Processing
    "load_normalized_csv",
    "load_clean_excel_sheet",
    "get_seeding_active_years",
    # Text Manipulation & Formatting
    "clean_text",
    "remove_diacritics",
    "fold_for_comparison",
    "generate_technical_slug",
    "truncate_text",
    "normalize_key",
    "extract_numeric_suffix",
    "compute_hierarchical_order",
    "cast_to_database_numeric",
]
