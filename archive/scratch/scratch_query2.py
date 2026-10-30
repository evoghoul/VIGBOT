import sqlite3

db_path = r"C:\StudentHelpdesk\database\student_helpdesk.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT * FROM knowledge_procedure_step WHERE procedure_id='p1' ORDER BY step_order")
for row in cursor.fetchall():
    print(row)

conn.close()
