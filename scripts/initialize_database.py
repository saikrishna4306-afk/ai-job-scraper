import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from database.database import create_session_factory

if __name__ == "__main__":
    create_session_factory()
    print("Database initialized")
