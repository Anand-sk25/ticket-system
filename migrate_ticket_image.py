import sqlite3
import os

db_path = 'instance/mgm_events.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("Adding ticket_image_filename column to event table...")
        cursor.execute("ALTER TABLE event ADD COLUMN ticket_image_filename VARCHAR(200)")
        print("Column added successfully.")
    except sqlite3.OperationalError:
        print("ticket_image_filename column already exists.")
        
    conn.commit()
    conn.close()
    print("Database schema updated.")
else:
    print(f"Database not found at {db_path}")
