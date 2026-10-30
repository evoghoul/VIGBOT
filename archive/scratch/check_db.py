import json
from app.database import get_db_connection
with get_db_connection() as conn:
    print(json.dumps([dict(r) for r in conn.execute("SELECT student_id, course_title FROM attendance").fetchall()], indent=2))
    print("---")
    print(json.dumps([dict(r) for r in conn.execute("SELECT student_id, full_name FROM students").fetchall()], indent=2))
