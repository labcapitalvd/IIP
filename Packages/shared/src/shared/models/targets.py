from shared.db import TableInfo


class CoreTargetTable:
    # --- Reference Schema ---
    LOG_ACTION_TYPES = TableInfo("log_action_types", "reference")
    FILE_TYPES = TableInfo("file_types", "reference")
    USER_TIERS = TableInfo("user_tiers", "reference")
    ACCESS_LEVELS = TableInfo("access_levels", "reference")
    SYSTEM_ROLES = TableInfo("system_roles", "reference")
    COMMENT_TYPES = TableInfo("comment_types", "reference")
    NOTIFICATION_TYPES = TableInfo("notification_types", "reference")

    # --- Auth Schema ---
    USERS = TableInfo("users", "auth")
    REFRESH_SESSIONS = TableInfo("refresh_sessions", "auth")
    USER_DETAILS = TableInfo("user_details", "auth")
    USER_PROFILES = TableInfo("user_profiles", "auth")

    # --- Audit & Files Schema ---
    LOGS = TableInfo("logs", "audit")
    FILES = TableInfo("files", "files")

    # --- Links Schema ---
    LINK_USER_FILE = TableInfo("user_file_links", "links")
    LINK_USER_SYSTEM_ROLE = TableInfo("user_system_role_links", "links")

    # --- Interactions Schema ---
    COMMENTS = TableInfo("comments", "interactions")
    NOTIFICATIONS = TableInfo("notifications", "interactions")


class TargetTable(CoreTargetTable):
    # --- Actors Schema ---
    ACTOR_SEGMENTS = TableInfo("actor_segments", "actors")
    ACTORS = TableInfo("actors", "actors")
    LINK_USER_ACTOR = TableInfo("user_actor_links", "links")

    # --- Reference Schema (Extended) ---
    FIELD_TYPES = TableInfo("field_types", "reference")
    RELATIONAL_OPERATORS = TableInfo("relational_operators", "reference")
    RULE_TYPES = TableInfo("rule_types", "reference")
    SUBMISSION_STATUS_TYPES = TableInfo("submission_status_types", "reference")

    # --- Forms Schema ---
    FORMS = TableInfo("forms", "forms")
    SECTION_TYPES = TableInfo("section_types", "forms")
    SECTIONS = TableInfo("sections", "forms")
    INFORMATIONS = TableInfo("information", "forms")
    QUESTIONS = TableInfo("questions", "forms")
    CARD_TEMPLATES = TableInfo("card_templates", "forms")
    FIELD_GROUPS = TableInfo("field_groups", "forms")
    FIELDS = TableInfo("fields", "forms")
    FIELD_CHOICES = TableInfo("field_choices", "forms")

    # --- Rules Schema ---
    SECTION_DEPENDENCIES = TableInfo("section_dependencies", "rules")
    FIELD_DEPENDENCIES = TableInfo("field_dependencies", "rules")
    FIELD_RULES = TableInfo("field_rules", "rules")

    # --- Submissions & Grading Schemas ---
    SUBMISSIONS = TableInfo("submissions", "submissions")
    ASSIGNMENTS = TableInfo("assignments", "grading")
    CRITERIA = TableInfo("criteria", "grading")
    GRADES = TableInfo("grades", "grading")
    RESULTS = TableInfo("results", "grading")

    # --- Answers & Submission Links ---
    ANSWERS_CARD_ENTRY = TableInfo("answers_card_entry", "submissions")
    ANSWERS = TableInfo("answers", "submissions")
    ANSWERS_BOOLEAN = TableInfo("answers_boolean", "submissions")
    ANSWERS_DATE = TableInfo("answers_date", "submissions")
    ANSWERS_FILE = TableInfo("answers_file", "submissions")
    ANSWERS_MULTI_CHOICE = TableInfo("answers_multi_choice", "submissions")
    ANSWERS_NUMERIC = TableInfo("answers_numeric", "submissions")
    ANSWERS_SINGLE_CHOICE = TableInfo("answers_single_choice", "submissions")
    ANSWERS_TEXT = TableInfo("answers_texts", "submissions")
    LINK_USER_SUBMISSION = TableInfo("user_submission_links", "links")
    LINK_CHOICE_MULTICHOICE = TableInfo("choice_multichoice_links", "links")
