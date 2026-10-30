import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = r"c:\StudentHelpdesk\database\student_helpdesk.db"

def setup_lost_and_found_table():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Create lost_and_found table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS lost_and_found (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('lost', 'found')),
            title TEXT NOT NULL,
            description TEXT,
            tags TEXT,
            contact_info TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('open', 'claimed')),
            date_posted TEXT NOT NULL,
            image_url TEXT
        )
        ''')
        
        # Clear existing to be idempotent
        cursor.execute("DELETE FROM lost_and_found")

        now = datetime.now()
        
        items = [
            (
                '251FA04E13',
                'lost',
                'Blue Water Bottle',
                'Lost my blue Milton water bottle near the Library entrance yesterday evening.',
                'bottle, library',
                'aman@vignan.edu',
                'open',
                (now - timedelta(days=1)).isoformat(),
                'https://images.unsplash.com/photo-1602143407151-7111542de6e8?auto=format&fit=crop&w=400&q=80'
            ),
            (
                '191FA04E22',
                'found',
                'Scientific Calculator',
                'Found a Casio fx-991EX calculator in Room N-312 after the morning lecture.',
                'calculator, electronics, N-312',
                'john.doe@vignan.edu',
                'open',
                (now - timedelta(hours=5)).isoformat(),
                'https://images.unsplash.com/photo-1594980596870-8aa52a78d8cd?auto=format&fit=crop&w=400&q=80'
            ),
            (
                '201FA04E33',
                'lost',
                'Student ID Card',
                'Lost my ID card in the main cafeteria. Name: Sarah Smith.',
                'id card, cafeteria',
                'sarah.s@vignan.edu',
                'open',
                (now - timedelta(days=2)).isoformat(),
                'https://images.unsplash.com/photo-1605370397500-2d83296c07a3?auto=format&fit=crop&w=400&q=80'
            ),
            (
                '211FA04E44',
                'found',
                'Set of Keys',
                'Found a keychain with 3 keys and a Marvel logo near the sports complex.',
                'keys, sports complex',
                'mike.r@vignan.edu',
                'open',
                (now - timedelta(hours=2)).isoformat(),
                'https://images.unsplash.com/photo-1582139329536-e7284fece509?auto=format&fit=crop&w=400&q=80'
            ),
             (
                '221FA04E55',
                'lost',
                'Airpods Pro (Left earbud)',
                'Dropped my left earbud somewhere between the IT block and the main gate.',
                'electronics, airpods',
                'emma.w@vignan.edu',
                'claimed',
                (now - timedelta(days=5)).isoformat(),
                'https://images.unsplash.com/photo-1588423771073-b8903fbb85b5?auto=format&fit=crop&w=400&q=80'
            )
        ]

        # Insert items
        cursor.executemany('''
        INSERT INTO lost_and_found (student_id, type, title, description, tags, contact_info, status, date_posted, image_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', items)
        
        conn.commit()
        print(f"Lost & Found items seeded successfully. Inserted {len(items)} items.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    setup_lost_and_found_table()
