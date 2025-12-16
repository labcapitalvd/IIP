from logging.config import fileConfig

from alembic import context

from shared_db import sync_engine, SYNC_DB

from shared_db import Base
from shared_models import __all__ as model_names


def print_list(title: str, items: list[str], cols: int = 3):
    print(f"\n{title}:")
    width = max(len(item) for item in items) + 2
    for i, item in enumerate(sorted(items)):
        print(f"{item:<{width}}", end="" if (i + 1) % cols else "\n")
    if len(items) % cols:
        print()

print_list("Loaded Models", model_names)
print_list("Tables Found in Metadata", list(Base.metadata.tables.keys()))

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config
config.set_main_option("sqlalchemy.url", SYNC_DB)

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


def run_migrations_offline() -> None:
    context.configure(
        url=SYNC_DB,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


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


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
