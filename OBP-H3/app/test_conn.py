from app.db import get_conn
c = get_conn()
cur = c.cursor()
cur.execute("SELECT TOP 1 name FROM sys.databases")
print("Konekcija OK ->", cur.fetchone()[0])
c.close()
