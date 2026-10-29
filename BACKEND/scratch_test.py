import psycopg
conn = psycopg.connect('postgresql://postgres:postgrespassword@localhost:5432/vigbot')
cur = conn.cursor()
try:
    cur.execute("SELECT pg_get_serial_sequence('studentlife_club_application', 'id')")
    print("Serial sequence:", cur.fetchone())
    cur.execute("SELECT MAX(id) FROM studentlife_club_application")
    print("Max ID:", cur.fetchone())
except Exception as e:
    print("Error:", e)
