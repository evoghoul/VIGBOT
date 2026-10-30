import sqlite3

db_path = r"C:\StudentHelpdesk\database\student_helpdesk.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- Students Departments ---")
cursor.execute("SELECT DISTINCT department_code, programme_name FROM students")
for row in cursor.fetchall():
    print(row)

print("\n--- Faculty ---")
cursor.execute("SELECT name, department, role, cabin FROM faculty WHERE role='HOD'")
for row in cursor.fetchall():
    print(row)

print("\n--- Campus Locations ---")
cursor.execute("SELECT * FROM campus_locations")
for row in cursor.fetchall():
    print(row)

print("\n--- Procedures ---")
cursor.execute("SELECT * FROM knowledge_procedure")
for row in cursor.fetchall():
    print(row)

conn.close()
