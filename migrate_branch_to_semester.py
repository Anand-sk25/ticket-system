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
        # Check if semester column already exists
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'semester' not in columns:
            print("Adding 'semester' column to 'user' table...")
            cursor.execute("ALTER TABLE user ADD COLUMN semester VARCHAR(100)")
            
            if 'branch' in columns:
                cursor.execute("UPDATE user SET semester = branch")
                print("Successfully migrated 'branch' data to 'semester' column.")
            else:
                print("Note: 'branch' column does not exist to migrate data from.")
        else:
            print("'semester' column already exists.")
            
        conn.commit()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()
        print("Done.")

if __name__ == '__main__':
    migrate()
