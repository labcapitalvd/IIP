"""Poblado de permisos atómicos y granulares (Permission)"""

from shared.db import SessionSync
from shared.enums import PermissionsEnum
from shared.models import Permission
from shared.utils.logger import get_logger
from sqlalchemy import select

logger = get_logger(__name__)


def upgrade() -> None:
    added_count = 0
    skipped_count = 0

    with SessionSync() as session:
        # Fetch all existing permission codes in 1 single query
        existing_codes = set(session.scalars(select(Permission.code)).all())

        new_records: list[Permission] = []

        for perm_enum in PermissionsEnum:
            if perm_enum.code in existing_codes:
                logger.debug(
                    f"Permission '{perm_enum.code}' already exists in Permission"
                )
                skipped_count += 1
                continue

            new_records.append(
                Permission(
                    key=perm_enum.key,
                    code=perm_enum.code,
                    label=perm_enum.label,
                    description=perm_enum.description,
                )
            )
            logger.debug(f"Queued '{perm_enum.code}' for Permission")
            added_count += 1

        # Bulk insert all new permissions at once
        if new_records:
            session.add_all(new_records)
            session.commit()

    logger.info(
        f"Permission seed complete: {added_count} added, {skipped_count} skipped."
    )
