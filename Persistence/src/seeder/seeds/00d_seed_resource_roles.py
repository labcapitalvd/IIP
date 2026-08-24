"""Poblado de roles de recursos ReBAC (ResourceRole)"""

from shared.db import SessionSync
from shared.enums import ResourceRolesEnum
from shared.models import ResourceRole
from shared.utils.logger import getLogger
from sqlalchemy import select

logger = getLogger(__name__)


def upgrade() -> None:
    added_count = 0
    skipped_count = 0

    with SessionSync() as session:
        # Fetch all existing resource role codes in 1 single query
        existing_codes = set(session.scalars(select(ResourceRole.code)).all())

        new_records: list[ResourceRole] = []

        for role_enum in ResourceRolesEnum:
            if role_enum.code in existing_codes:
                logger.debug(
                    f"ResourceRole '{role_enum.code}' already exists in ResourceRole"
                )
                skipped_count += 1
                continue

            new_records.append(
                ResourceRole(
                    code=role_enum.code,
                    label=role_enum.label,
                    description=role_enum.description,
                )
            )
            logger.debug(f"Queued '{role_enum.code}' for ResourceRole")
            added_count += 1

        # Bulk insert all new resource roles at once
        if new_records:
            session.add_all(new_records)
            session.commit()

    logger.debug(
        f"ResourceRole seed complete: {added_count} added, {skipped_count} skipped."
    )
