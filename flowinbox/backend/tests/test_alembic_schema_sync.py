import pytest
from scripts.verify_alembic_schema import verify_schema


def test_alembic_schema_sync():
    """Verify that Alembic migrations head matches Base.metadata with zero missing tables/columns."""
    assert verify_schema() is True
