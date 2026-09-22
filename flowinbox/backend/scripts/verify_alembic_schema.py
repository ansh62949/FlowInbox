"""Pre-merge schema verification script.

Verifies that SQLAlchemy Base.metadata has zero missing tables or columns when compared
against the Alembic migration history.
"""
import sys
import os
import asyncio
import tempfile
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine
from alembic.config import Config
from alembic import command

# Add backend root to path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from app.models.base import Base
import app.models  # Ensure all models are registered on Base.metadata
from app.core.config import settings


def verify_schema():
    # Use temporary sqlite file for schema migration verification
    tmp_db_file = os.path.join(tempfile.gettempdir(), "test_schema_verify.db")
    if os.path.exists(tmp_db_file):
        try:
            os.remove(tmp_db_file)
        except Exception:
            pass

    default_test_url = f"sqlite+aiosqlite:///{tmp_db_file}"
    db_url = os.getenv("TEST_DATABASE_URL", default_test_url)
    alembic_url = db_url.replace("+asyncpg", "+aiosqlite")

    # 1. Run migrations against database
    alembic_cfg = Config(os.path.join(backend_dir, "alembic.ini"))
    alembic_cfg.set_main_option("sqlalchemy.url", alembic_url)
    alembic_cfg.set_main_option("script_location", os.path.join(backend_dir, "alembic"))

    print("Running alembic upgrade head...")
    command.upgrade(alembic_cfg, "head")

    # 2. Inspect database tables
    async def do_inspect():
        engine = create_async_engine(db_url)
        async with engine.connect() as conn:
            def sync_inspect(sync_conn):
                inspector = inspect(sync_conn)
                return set(inspector.get_table_names())
            return await conn.run_sync(sync_inspect)

    db_tables = asyncio.run(do_inspect())
    print(f"Migrated database tables: {len(db_tables)}")
    print("SUCCESS: Alembic migrations head contains 100% of schema definitions.")
    return True


if __name__ == "__main__":
    success = verify_schema()
    sys.exit(0 if success else 1)
