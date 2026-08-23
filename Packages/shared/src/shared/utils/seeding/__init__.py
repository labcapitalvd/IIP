# shared/utils/seeding/__init__.py

from .assertions import (
    assert_all_uuidv7,
    assert_no_duplicates,
    assert_no_missing,
)
from .ids import is_uuidv7, new_uuidv7
from .introspection import (
    assert_field_lengths,
    get_table_columns,
    validate_required_columns,
)
from .io import get_seeding_active_years, load_clean_excel_sheet, load_normalized_csv
from .text import (
    cast_to_database_numeric,
    clean_text,
    compute_hierarchical_order,
    extract_numeric_suffix,
    fold_for_comparison,
    generate_technical_slug,
    normalize_key,
    remove_diacritics,
    truncate_text,
)

__all__ = [
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
