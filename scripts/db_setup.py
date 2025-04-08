import sqlite3
from pathlib import Path

DB_PATH = Path("database/exports.db")

def setup_database():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS export_status
                (task_id TEXT PRIMARY KEY,
                 status TEXT,
                 start_time INTEGER,
                 end_time INTEGER,
                 last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    print("Database initialized successfully")

if __name__ == "__main__":
    setup_database()
