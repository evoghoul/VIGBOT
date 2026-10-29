import sqlite3; conn = sqlite3.connect("database/vigbot.db"); print(conn.execute("PRAGMA table_info(studentlife_club_member)").fetchall())
