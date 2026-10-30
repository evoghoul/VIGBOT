import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = r"c:\StudentHelpdesk\database\student_helpdesk.db"

def setup_calendar_table():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Create calendar_events table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS calendar_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            type TEXT NOT NULL,
            location TEXT
        )
        ''')
        
        # Clear existing mock events for this student if any (to make script idempotent)
        cursor.execute("DELETE FROM calendar_events WHERE student_id = '251FA04E13'")

        # Generate some mock data around the current date
        now = datetime.now()
        # Find the Monday of the current week
        start_of_week = now - timedelta(days=now.weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)

        events = []
        
        # Monday
        mon = start_of_week
        events.extend([
            ('251FA04E13', 'Data Structures', 'CS201 Lecture', (mon + timedelta(hours=9)).isoformat(), (mon + timedelta(hours=10, minutes=30)).isoformat(), 'Lecture', 'Room N-312'),
            ('251FA04E13', 'Digital Logic', 'EC201 Lecture', (mon + timedelta(hours=11)).isoformat(), (mon + timedelta(hours=12, minutes=30)).isoformat(), 'Lecture', 'Room N-312'),
            ('251FA04E13', 'Robotics Club Meetup', 'Weekly planning', (mon + timedelta(hours=16)).isoformat(), (mon + timedelta(hours=17, minutes=30)).isoformat(), 'Club', 'Innovation Lab'),
        ])

        # Tuesday
        tue = start_of_week + timedelta(days=1)
        events.extend([
            ('251FA04E13', 'Data Structures Lab', 'Lab session', (tue + timedelta(hours=10)).isoformat(), (tue + timedelta(hours=13)).isoformat(), 'Lab', 'Lab-4'),
            ('251FA04E13', 'Web Development', 'CS202 Lecture', (tue + timedelta(hours=14)).isoformat(), (tue + timedelta(hours=15, minutes=30)).isoformat(), 'Lecture', 'Room N-312'),
        ])

        # Wednesday
        wed = start_of_week + timedelta(days=2)
        events.extend([
            ('251FA04E13', 'Computer Networks', 'CS203 Lecture', (wed + timedelta(hours=9)).isoformat(), (wed + timedelta(hours=10, minutes=30)).isoformat(), 'Lecture', 'Room N-312'),
            ('251FA04E13', 'Database Systems', 'CS204 Lecture', (wed + timedelta(hours=11)).isoformat(), (wed + timedelta(hours=12, minutes=30)).isoformat(), 'Lecture', 'Room N-312'),
            ('251FA04E13', 'AI Workshop', 'Guest lecture on ML', (wed + timedelta(hours=15)).isoformat(), (wed + timedelta(hours=17)).isoformat(), 'Event', 'Main Auditorium'),
        ])

        # Thursday
        thu = start_of_week + timedelta(days=3)
        events.extend([
            ('251FA04E13', 'Web Development Lab', 'React & Next.js', (thu + timedelta(hours=9)).isoformat(), (thu + timedelta(hours=12)).isoformat(), 'Lab', 'Lab-5'),
            ('251FA04E13', 'Midterm Exam: Data Structures', 'Important', (thu + timedelta(hours=14)).isoformat(), (thu + timedelta(hours=16)).isoformat(), 'Exam', 'Exam Hall A'),
        ])

        # Friday
        fri = start_of_week + timedelta(days=4)
        events.extend([
            ('251FA04E13', 'Computer Networks Lab', 'Cisco Packet Tracer', (fri + timedelta(hours=10)).isoformat(), (fri + timedelta(hours=13)).isoformat(), 'Lab', 'Lab-1'),
            ('251FA04E13', 'Database Systems Lab', 'SQL practice', (fri + timedelta(hours=14)).isoformat(), (fri + timedelta(hours=16)).isoformat(), 'Lab', 'Lab-2'),
            ('251FA04E13', 'Hackathon Kickoff', '24-hour coding challenge', (fri + timedelta(hours=18)).isoformat(), (fri + timedelta(hours=19)).isoformat(), 'Event', 'Innovation Lab'),
        ])

        # Insert events
        cursor.executemany('''
        INSERT INTO calendar_events (student_id, title, description, start_time, end_time, type, location)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', events)
        
        conn.commit()
        print(f"Calendar events seeded successfully. Inserted {len(events)} events.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    setup_calendar_table()
