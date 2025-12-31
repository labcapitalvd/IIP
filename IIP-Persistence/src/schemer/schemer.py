from sqlalchemy.exc import ProgrammingError
from sqlalchemy.schema import CreateSchema

from shared_db import SessionSync, merge_enums
from shared_models.targets import TargetTable as TargetTableBase
from shared_utils import get_logger

from models.targets import TargetTable as TargetTableApp


TargetTable = merge_enums(
    "TargetTable",
    TargetTableBase,
    TargetTableApp
)


logger = get_logger("seed/schema")



def main():
    created = []
    skipped = []
    failed = []

    with SessionSync() as session:
        schemas = {table.schema for table in TargetTable}

        for schema in schemas:
            try:
                logger.info(f"Creating schema '{schema}'…")
                session.execute(CreateSchema(schema, if_not_exists=True))
                session.commit()

                # If `if_not_exists=True`, PostgreSQL won't error
                # but SQLAlchemy doesn't tell us explicitly if created or skipped.
                # However, PostgreSQL returns no error:
                created.append(schema)

            except ProgrammingError as e:
                # Detect "schema already exists"
                # PostgreSQL error code: '42P06'
                # Example: e.orig.pgcode
                if hasattr(e.orig, "pgcode") and e.orig.pgcode == "42P06":
                    logger.info(f"Schema '{schema}' already exists — skipped.")
                    skipped.append(schema)
                    session.rollback()
                else:
                    logger.error(f"Failed to create schema '{schema}': {e}")
                    failed.append(schema)
                    session.rollback()

            except Exception as e:
                logger.error(f"Unexpected error creating schema '{schema}': {e}")
                failed.append(schema)
                session.rollback()

    # Summary
    logger.info("---- Schema Creation Summary ----")
    logger.info(f"Created ({len(created)}): {created}")
    logger.info(f"Skipped ({len(skipped)}): {skipped}")
    logger.info(f"Failed  ({len(failed)}): {failed}")

    print("---- Schema Creation Summary ----")
    print(f"Created ({len(created)}): {created}")
    print(f"Skipped ({len(skipped)}): {skipped}")
    print(f"Failed  ({len(failed)}): {failed}")

    return created, skipped, failed


if __name__ == "__main__":
    main()
