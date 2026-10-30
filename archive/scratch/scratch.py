import sys
import os
sys.path.insert(0, os.path.abspath("."))
from dotenv import load_dotenv
load_dotenv()

from app.database import is_postgres_configured, get_db_connection

print("Postgres configured:", is_postgres_configured())
print("DATABASE_URL:", os.environ.get("DATABASE_URL"))

try:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT pg_get_serial_sequence('studentlife_club_application', 'id');")
    seq = cur.fetchone()
    print("Sequence name:", seq)
    if seq and seq[0] is None:
        print("Sequence is null? Maybe the table doesn't have it bound.")
        # Try finding sequence manually
        cur.execute("SELECT c.relname FROM pg_class c WHERE c.relkind = 'S' AND c.relname LIKE 'studentlife_club_application%';")
        print("Found sequences:", cur.fetchall())
except Exception as e:
    print("Error:", e)
