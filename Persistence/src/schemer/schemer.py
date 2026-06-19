import inspect

from shared.models.targets import TargetTable
from shared.db import SessionSync, TableInfo
from shared.utils.logger import get_logger
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.schema import CreateSchema

from shared.utils import print_list

logger = get_logger("seed/schema")


def get_all_schemas():
    """Extracts unique schemas from TargetTable and its parents."""
    schemas = set()
    # Iterate through TargetTable and its base classes (CoreTargetTable)
    for cls in inspect.getmro(TargetTable):
        for name, value in vars(cls).items():
            if isinstance(value, TableInfo):
                schemas.add(value.schema)
    return schemas


def main():
    created = []
    failed = []

    schemas = get_all_schemas()

    with SessionSync() as session:
        for schema in schemas:
            try:
                logger.info(f"Ensuring schema '{schema}' exists…")
                # if_not_exists=True prevents Postgres from raising 42P06
                session.execute(CreateSchema(schema, if_not_exists=True))
                session.commit()
                created.append(schema)
            except SQLAlchemyError as e:
                session.rollback()
                logger.error(f"Failed to ensure schema '{schema}': {e}")
                failed.append(schema)

    # Summary
    logger.info("---- Schema Creation Summary ----")
    logger.info(f"Created ({len(created)}): {created}")
    logger.info(f"Failed  ({len(failed)}): {failed}")

    print_list("Created", created)
    print_list("Failed", failed)

    return created, failed


if __name__ == "__main__":
    main()
