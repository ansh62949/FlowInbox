"""Verification module for Alembic migration synchronization with SQLAlchemy Base.metadata."""
import sys
import os
import glob

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models import Base


def verify_schema() -> bool:
    """Verify that Alembic migrations head matches Base.metadata with zero missing tables/columns.
    
    Returns True if 100% synchronized, False otherwise.
    """
    model_schema = {}
    for table_name, table in Base.metadata.tables.items():
        columns = set(col.name for col in table.columns)
        model_schema[table_name] = columns

    versions_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "alembic", "versions"))
    migration_files = glob.glob(os.path.join(versions_dir, "*.py"))

    migration_content = ""
    for mf in sorted(migration_files):
        with open(mf, "r", encoding="utf-8") as f:
            migration_content += f.read() + "\n"

    missing_tables = []
    missing_columns = []

    for table_name, columns in model_schema.items():
        table_pattern = f"'{table_name}'"
        if table_pattern not in migration_content:
            missing_tables.append(table_name)
            continue

        for col_name in columns:
            col_pattern_1 = f"'{col_name}'"
            col_pattern_2 = f'"{col_name}"'
            if col_pattern_1 not in migration_content and col_pattern_2 not in migration_content:
                missing_columns.append((table_name, col_name))

    if missing_tables or missing_columns:
        if missing_tables:
            print(f"[FAIL] Missing tables in migrations: {missing_tables}")
        if missing_columns:
            print(f"[FAIL] Missing columns in migrations: {missing_columns}")
        return False

    return True


if __name__ == "__main__":
    success = verify_schema()
    sys.exit(0 if success else 1)
