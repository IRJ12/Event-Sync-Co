import os
import sqlite3
from app import create_app, db

def fix_database():
    app = create_app()
    with app.app_context():
        # Connect to the database
        db_path = os.path.join(app.instance_path, 'school_events.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Add the image_path column if it doesn't exist
            cursor.execute("""
                PRAGMA table_info(events)
            """)
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'image_path' not in columns:
                print("Adding image_path column to events table...")
                cursor.execute("""
                    ALTER TABLE events ADD COLUMN image_path VARCHAR(200)
                """)
                conn.commit()
                print("Successfully added image_path column!")
            else:
                print("image_path column already exists")
                
        except Exception as e:
            print(f"Error: {e}")
            conn.rollback()
        finally:
            conn.close()

if __name__ == '__main__':
    fix_database()
