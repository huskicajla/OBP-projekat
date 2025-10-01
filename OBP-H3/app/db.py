import os, pyodbc
from dotenv import load_dotenv

load_dotenv()

SERVER = os.getenv("DB_SERVER", "localhost")
DBNAME = os.getenv("DB_NAME", "StackOverflow2013")
AUTH   = os.getenv("DB_AUTH", "windows").lower()

PREF = ["ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server", "SQL Server"]
avail = set(pyodbc.drivers())
DRIVER = next((d for d in PREF if d in avail), None)
if not DRIVER:
    raise RuntimeError(f"Nema SQL Server ODBC drivera. Nađeno: {sorted(avail)}")

def _conn_str() -> str:
    if AUTH == "windows":
        return f"DRIVER={{{DRIVER}}};SERVER={SERVER};DATABASE={DBNAME};Trusted_Connection=yes;TrustServerCertificate=yes;"
    else:
        USER = os.getenv("DB_USER",""); PWD = os.getenv("DB_PASSWORD","")
        return f"DRIVER={{{DRIVER}}};SERVER={SERVER};DATABASE={DBNAME};UID={USER};PWD={PWD};TrustServerCertificate=yes;"

def get_conn(autocommit: bool=False) -> pyodbc.Connection:
    return pyodbc.connect(_conn_str(), autocommit=autocommit)
