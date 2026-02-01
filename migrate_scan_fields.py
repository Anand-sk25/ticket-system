import sqlite3
import os

db_path = 'instance/mgm_events.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("Adding is_scanned column...")
        cursor.execute("ALTER TABLE ticket ADD COLUMN is_scanned BOOLEAN DEFAULT 0")
    except sqlite3.OperationalError:
        print("is_scanned column already exists.")
        
    try:
        print("Adding scanned_at column...")
        cursor.execute("ALTER TABLE ticket ADD COLUMN scanned_at DATETIME")
    except sqlite3.OperationalError:
        print("scanned_at column already exists.")
        
    conn.commit()
    conn.close()
    print("Database schema updated.")
else:
    print(f"Database not found at {db_path}")
