import asyncio
from logging.config import fileConfig
import sqlalchemy as sa
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

import sys
import os
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.config import settings
from app.db.base import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

import re

def sanitize_db_url(url: str) -> str:
    """Sanitize postgresql+asyncpg database URL by converting libpq sslmode params."""
    if "asyncpg" in url and "sslmode=" in url:
        url = url.replace("sslmode=require", "ssl=require")
        url = url.replace("sslmode=prefer", "ssl=prefer")
        url = url.replace("sslmode=disable", "ssl=disable")
        url = url.replace("sslmode=verify-full", "ssl=verify-full")
        url = re.sub(r'[\?&]sslmode=[^&]+', '', url)
    return url

# Fallback to application settings if sqlalchemy.url is not explicitly set
target_url = config.get_main_option("sqlalchemy.url") or settings.DATABASE_URL
config.set_main_option("sqlalchemy.url", sanitize_db_url(target_url))






def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_num_dim=255,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    # Ensure alembic_version table exists with VARCHAR(255) so long revision IDs fit
    connection.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS alembic_version (
            version_num VARCHAR(255) NOT NULL,
            CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
        );
    """))
    if connection.dialect.name == "postgresql":
        connection.execute(sa.text("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(255);"))


    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        version_num_dim=255,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
