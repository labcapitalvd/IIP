from enum import Enum
from decimal import Decimal


class RolesEnum(Enum):
    """What different roles a user can have in a form."""
    OWNER = "owner"  # Full control over the submission or actor
    CONTRIBUTOR = "contributor"  # Can fill/edit forms, upload files, etc.
    REVIEWER = "reviewer"  # Can comment or suggest changes
    APPROVER = "approver"  # Can finalize and submit
    OBSERVER = "observer"  # Read-only access

    def __init__(self, description: str):
        self.description = description

    @property
    def label(self):
        return self.name


class UserTiersEnum(Enum):
    """What different priorities and access a user has on the app"""
    ROOT = (Decimal(500 * 1024 * 1024), Decimal(100 * 1024 * 1024 * 1024), 500, 5)
    ADMIN = (Decimal(100 * 1024 * 1024), Decimal(50 * 1024 * 1024 * 1024), 300, 4)
    PREMIUM = (Decimal(50 * 1024 * 1024), Decimal(20 * 1024 * 1024 * 1024), 120, 3)
    STANDARD = (Decimal(10 * 1024 * 1024), Decimal(10 * 1024 * 1024 * 1024), 60, 2)
    GUEST = (Decimal(5 * 1024 * 1024), Decimal(5 * 1024 * 1024 * 1024), 30, 1)

    def __init__(
        self, max_file_size, storage_quota, max_requests_per_minute, priority_level
    ):
        self.max_file_size = max_file_size
        self.storage_quota = storage_quota
        self.max_requests_per_minute = max_requests_per_minute
        self.priority_level = priority_level

    @property
    def label(self):
        return self.name  # Use the enum member name itself


