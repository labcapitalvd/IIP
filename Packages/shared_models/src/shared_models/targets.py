from shared_db import TableInfo

class CoreTargetTable:
    LOG_ACTION_TYPES = TableInfo("log_action_types", "reference")
    FILE_TYPES = TableInfo("file_types", "reference")
    ROLES = TableInfo("roles", "reference")
    USER_TIERS = TableInfo("user_tiers", "reference")

    USERS = TableInfo("users", "auth")
    LOGS = TableInfo("logs", "audit")
    REFRESH_SESSIONS = TableInfo("refresh_sessions", "auth")
    USER_DETAILS = TableInfo("user_details", "auth")
    FILES = TableInfo("files", "files")
    USER_PROFILES = TableInfo("user_profiles", "auth")
    LINK_USER_FILE = TableInfo("user_file_links", "links")

    COMMENT_TYPES = TableInfo("comment_types", "reference")
    NOTIFICATION_TYPES = TableInfo("notification_types", "reference")
    COMMENTS = TableInfo("comments", "interactions")
    NOTIFICATIONS = TableInfo("notifications", "interactions")
