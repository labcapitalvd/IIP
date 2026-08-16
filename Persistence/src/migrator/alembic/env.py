from logging.config import fileConfig

from alembic import context

from shared.infrastructure import sync_engine, SYNC_URL
from shared.db import Base
from shared.models import __all__ as model_names
from shared.utils import format_banner, format_list
from shared.utils.logger import get_logger, configure_logging

import math

# Initialize global logging configuration
configure_logging()
logger = get_logger(__name__)

logger.info(format_banner("ALEMBIC MIGRATIONS"))
logger.info(format_list("Loaded Models", model_names))
logger.info(format_list("Tables Found in Metadata", list(Base.metadata.tables.keys())))

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config
config.set_main_option("sqlalchemy.url", SYNC_URL)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

logger.info(format_banner("ALEMBIC PROCESS COMPLETE"))


def run_migrations_offline() -> None:
    context.configure(
        url=SYNC_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()
    logger.info("Offline migrations completed successfully.")


def run_migrations_online() -> None:
    connectable = sync_engine

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table="alembic_automatic_version",
        )

        with context.begin_transaction():
            context.run_migrations()
    logger.info("Online migrations completed successfully.")


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
