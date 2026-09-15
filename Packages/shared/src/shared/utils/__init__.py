from .encryption import decrypt, encrypt
from .error_handling import (
    BaseDomainError,
    domain_exception_handler,
    universal_exception_handler,
    validation_exception_handler,
)
from .files import (
    FileError,
    FileExtensionError,
    FileNameError,
    FileOSError,
    FileUtils,
    delete_file,
    rename_file,
    save_file,
)
from .hashing import (
    hash_password,
    hash_string,
    hash_token,
    verify_password,
    verify_string,
    verify_token,
)
from .logger import configure_logging, getLogger
from .seeding import (
    assert_all_uuidv7,
    assert_field_lengths,
    assert_no_duplicates,
    assert_no_missing,
    cast_to_database_numeric,
    clean_text,
    compute_hierarchical_order,
    extract_numeric_suffix,
    fold_for_comparison,
    generate_technical_slug,
    get_seeding_active_years,
    get_table_columns,
    is_uuidv7,
    load_clean_excel_sheet,
    load_normalized_csv,
    new_uuidv7,
    normalize_key,
    remove_diacritics,
    truncate_text,
    validate_required_columns,
)
from .texts import format_banner, format_list, sanitize_email, sanitize_text
from .tokens import (
    AccessContext,
    SessionContext,
    decode_token,
    generate_token,
    get_claims,
)

# Alias for backwards compatibility
hash_text = hash_string

__all__ = [
    "encrypt",
    "decrypt",
    "BaseDomainError",
    "domain_exception_handler",
    "universal_exception_handler",
    "validation_exception_handler",
    "FileUtils",
    "save_file",
    "rename_file",
    "delete_file",
    "FileError",
    "FileNameError",
    "FileExtensionError",
    "FileOSError",
    "hash_password",
    "hash_token",
    "hash_string",
    "hash_text",
    "verify_password",
    "verify_token",
    "verify_string",
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
    "getLogger",
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

