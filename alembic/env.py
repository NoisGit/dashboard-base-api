"""Alembic environment configuration for async SQLModel."""

import asyncio
from logging.config import fileConfig

from sqlmodel import SQLModel

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

from src.config.config import settings

# Import all models so Alembic can detect them
from src.models import __all__ as _models  # pylint: disable=unused-import


# Alembic Config object
config = context.config  # pylint: disable=no-member

# Set the database URL programmatically from settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(  # pylint: disable=no-member
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    # pylint: disable=no-member
    with context.begin_transaction():
        context.run_migrations()
    # pylint: enable=no-member


def do_run_migrations(connection) -> None:
    """Run migrations using the provided connection."""
    # pylint: disable=no-member
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()
    # pylint: enable=no-member


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():  # pylint: disable=no-member
    run_migrations_offline()
else:
    asyncio.run(run_async_migrations())
