import sqlite3
import os

DB_PATH = r"c:\StudentHelpdesk\database\student_helpdesk.db"

def setup_admin_table():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Create admins table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT NOT NULL,
            role TEXT NOT NULL
        )
        ''')
        
        # In a real app we'd hash the password, but for this demo we'll store it as plain text 'admin123'
        # or a simple representation since it's a prototype
        cursor.execute('''
        INSERT OR IGNORE INTO admins (id, username, password_hash, name, role)
        VALUES ('ADM001', 'admin', 'admin123', 'Default Nodal Officer', 'Admin')
        ''')
        
        conn.commit()
        print("Admins table created and seeded successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    setup_admin_table()
