import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'instance', 'mgm_events.db')

def migrate():
    print(f"Connecting to database at: {db_path}")
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("PRAGMA table_info(event)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'is_seated' not in columns:
            print("Adding 'is_seated' column to 'event' table...")
            cursor.execute("ALTER TABLE event ADD COLUMN is_seated BOOLEAN DEFAULT 1")
            cursor.execute("UPDATE event SET is_seated = 1")
            print("Successfully migrated 'is_seated' column.")
        else:
            print("'is_seated' column already exists.")
            
        conn.commit()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()
        print("Done.")

if __name__ == '__main__':
    migrate()
