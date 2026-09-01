"""Run once to create SQLite tables: `python -m app.db.init_db`"""
from app.db.session import init_db

if __name__ == "__main__":
    init_db()
    print("Database initialized.")
