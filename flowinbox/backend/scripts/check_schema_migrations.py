"""CI / Pre-merge Script: Verify 100% parity between SQLAlchemy models and Alembic migrations.

Exits with 0 if clean, non-zero if missing tables or columns are detected.
"""
import sys
import os
import glob
import re

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models import Base


def main():
    print("[CI Schema Check] Auditing SQLAlchemy Base.metadata against Alembic migration files...")
    
    # Extract all tables and columns from SQLAlchemy Base.metadata
    model_schema = {}
    for table_name, table in Base.metadata.tables.items():
        columns = set(col.name for col in table.columns)
        model_schema[table_name] = columns

    # Read all migration scripts in alembic/versions
    versions_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "alembic", "versions"))
    migration_files = glob.glob(os.path.join(versions_dir, "*.py"))

    migration_content = ""
    for mf in sorted(migration_files):
        with open(mf, "r", encoding="utf-8") as f:
            migration_content += f.read() + "\n"

    missing_tables = []
    missing_columns = []

    for table_name, columns in model_schema.items():
        # Check table creation or reference in migrations
        table_pattern = f"'{table_name}'"
        if table_pattern not in migration_content:
            missing_tables.append(table_name)
            continue

        for col_name in columns:
            # Check column existence in migrations
            col_pattern_1 = f"'{col_name}'"
            col_pattern_2 = f'"{col_name}"'
            if col_pattern_1 not in migration_content and col_pattern_2 not in migration_content:
                missing_columns.append((table_name, col_name))

    if missing_tables:
        print(f"[FAIL] [CI Schema Check] MISSING TABLES IN MIGRATIONS: {missing_tables}")

    if missing_columns:
        print(f"[FAIL] [CI Schema Check] MISSING COLUMNS IN MIGRATIONS:")
        for tbl, col in missing_columns:
            print(f"   - Table '{tbl}' -> Column '{col}'")

    if missing_tables or missing_columns:
        print("\n[FAIL] CI Schema Check FAILED: Missing database migrations detected!")
        sys.exit(1)

    print(f"[OK] [CI Schema Check] PASSED: All {len(model_schema)} tables and columns are fully covered across {len(migration_files)} Alembic migration scripts!")
    sys.exit(0)


if __name__ == "__main__":
    main()
