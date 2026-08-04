from enum import Enum
from decimal import Decimal


class ResourceRolesEnum(Enum):
    """
    Scoped resource permissions used in link tables
    (UserFileLink, UserSubmissionLink, UserActorLink).
    Tuple: (code, label, description)
    """

    OWNER = (
        "owner",
        "Owner",
        "Full control over the entity, including deletion and permission management.",
    )
    EDITOR = (
        "editor",
        "Editor",
        "Can modify content, upload files, or edit form submission responses.",
    )
    EVALUATOR = (
        "evaluator",
        "Evaluator",
        "Can grade, score, and provide feedback on submissions or actors.",
    )
    COMMENTER = (
        "commenter",
        "Commenter",
        "Can add comments and discussions without modifying the core data.",
    )
    VIEWER = (
        "viewer",
        "Viewer",
        "Read-only access to the specific resource.",
    )

    def __init__(self, code: str, label: str, description: str):
        self.code = code
        self._label = label
        self.description = description

    @property
    def label(self) -> str:
        return self._label


class SystemRolesEnum(Enum):
    """
    Platform-wide global RBAC roles (UserSystemRoleLink).
    Tuple: (code, label, description)
    """

    PLATFORM_ADMIN = (
        "admin",
        "Platform Admin",
        "Full operational access across all tenants, user management, and system configs.",
    )
    FORM_BUILDER = (
        "form_builder",
        "Form Builder",
        "Can design, update, and deploy form templates and validation rules globally.",
    )
    GRADER = (
        "grader",
        "Grader / Evaluator",
        "Global access to evaluate assigned submissions across the platform.",
    )
    AUDITOR = (
        "auditor",
        "Auditor",
        "Read-only access to audit logs, system activity, and security records.",
    )
    STANDARD_USER = (
        "standard_user",
        "Standard User",
        "Default platform user capable of filling out forms and managing owned resources.",
    )

    def __init__(self, code: str, label: str, description: str):
        self.code = code
        self._label = label
        self.description = description

    @property
    def label(self) -> str:
        return self._label


class UserTiersEnum(Enum):
    """
    Platform tiers and quota limits (UserTier).
    Tuple: (code, label, max_file_size, storage_quota, max_requests_per_minute, priority_level)
    """

    ROOT = (
        "root",
        "Root / System",
        Decimal(500 * 1024 * 1024),  # 500 MB
        Decimal(100 * 1024 * 1024 * 1024),  # 100 GB
        500,
        5,
    )
    ADMIN = (
        "admin",
        "Administrator",
        Decimal(100 * 1024 * 1024),  # 100 MB
        Decimal(50 * 1024 * 1024 * 1024),  # 50 GB
        300,
        4,
    )
    PREMIUM = (
        "premium",
        "Premium Tier",
        Decimal(50 * 1024 * 1024),  # 50 MB
        Decimal(20 * 1024 * 1024 * 1024),  # 20 GB
        120,
        3,
    )
    STANDARD = (
        "standard",
        "Standard Tier",
        Decimal(10 * 1024 * 1024),  # 10 MB
        Decimal(10 * 1024 * 1024 * 1024),  # 10 GB
        60,
        2,
    )
    GUEST = (
        "guest",
        "Guest / Free Tier",
        Decimal(5 * 1024 * 1024),  # 5 MB
        Decimal(5 * 1024 * 1024 * 1024),  # 5 GB
        30,
        1,
    )

    def __init__(
        self,
        code: str,
        label: str,
        max_file_size: Decimal,
        storage_quota: Decimal,
        max_requests_per_minute: int,
        priority_level: int,
    ):
        self.code = code
        self._label = label
        self.max_file_size = max_file_size
        self.storage_quota = storage_quota
        self.max_requests_per_minute = max_requests_per_minute
        self.priority_level = priority_level

    @property
    def label(self) -> str:
        return self._label
