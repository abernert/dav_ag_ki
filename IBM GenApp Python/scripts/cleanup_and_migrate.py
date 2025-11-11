"""
Cleanup and migrate script for local dev (SQLite)

Actions:
- Deletes the local SQLite DB file to allow schema recreation.
- Recreates tables via app.init_db()
- Creates a unique index on policies.policy_number

Usage:
  python python_port/scripts/cleanup_and_migrate.py

Note: This is destructive. Use only if you are sure there is no data to keep.
"""
from __future__ import annotations

import os
from pathlib import Path
import sys

# Ensure python_port/ is importable as package root for `app.*`
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.main import init_db
from app.db.session import engine


def main() -> None:
    db_path = ROOT / "genapp.db"
    if db_path.exists():
        db_path.unlink()
        print(f"Removed {db_path}")

    # Recreate schema
    init_db()
    print("Database schema recreated.")

    # Create unique index for policy_number (global uniqueness)
    try:
        with engine.connect() as conn:
            conn.exec_driver_sql(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_policies_policy_number ON policies(policy_number)"
            )
            print("Ensured unique index uq_policies_policy_number")
    except Exception as e:
        print(f"Could not create unique index: {e}")


if __name__ == "__main__":
    main()
