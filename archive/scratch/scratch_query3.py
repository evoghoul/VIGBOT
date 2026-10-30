import sqlite3

db_path = r"C:\StudentHelpdesk\database\student_helpdesk.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT student_id, roll_no, full_name FROM students LIMIT 5")
for row in cursor.fetchall():
    print(row)

conn.close()
