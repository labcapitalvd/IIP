import inspect

from shared.db import SessionSync, TableInfo
from shared.models.targets import TargetTable
from shared.utils import format_banner, format_list
from shared.utils.logger import configure_logging, get_logger
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.schema import CreateSchema

logger = get_logger(__name__)


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
    configure_logging()

    successful_schema = []
    failed_schema = []

    logger.info(format_banner("DB SCHEME CREATION STARTING"))

    schemas = get_all_schemas()

    with SessionSync() as session:
        for schema in schemas:
            try:
                logger.debug(f"Ensuring schema '{schema}' exists…")
                # if_not_exists=True prevents Postgres from raising 42P06
                session.execute(CreateSchema(schema, if_not_exists=True))
                session.commit()
                successful_schema.append(schema)
            except SQLAlchemyError as e:
                session.rollback()
                logger.error(f"Failed to ensure schema '{schema}': {e}")
                failed_schema.append(schema)

    if successful_schema:
        logger.info(format_list("Created", successful_schema))
    if failed_schema:
        logger.info(format_list("Failed", failed_schema))

    logger.info(format_banner("DB SCHEME CREATION PROCESS COMPLETE"))

    return successful_schema, failed_schema


if __name__ == "__main__":
    main()
