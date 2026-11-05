"""Add new columns to existing SQLite database for international job support."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import Settings
from database.database import create_session_factory
from sqlalchemy import text

def migrate_jobs_table():
    """Add new columns to jobs table if they don't exist."""
    settings = Settings.load()
    Session = create_session_factory(settings)
    
    with Session() as session:
        # Check if country column exists
        result = session.execute(text("PRAGMA table_info(jobs)"))
        columns = {row[1] for row in result.fetchall()}
        
        new_columns = {
            "country": "TEXT",
            "shift_type": "TEXT",
            "work_hours": "TEXT",
            "expected_overlap": "TEXT",
            "salary_classification": "TEXT",
            "currency": "TEXT",
            "frequency": "TEXT",
        }
        
        for col_name, col_type in new_columns.items():
            if col_name not in columns:
                print(f"Adding column: {col_name} {col_type}")
                session.execute(text(f"ALTER TABLE jobs ADD COLUMN {col_name} {col_type}"))
                session.commit()
            else:
                print(f"Column {col_name} already exists, skipping")
        
        print("\n✅ Database migration completed successfully!")
        print("All new international job fields are now available.")

if __name__ == "__main__":
    migrate_jobs_table()
