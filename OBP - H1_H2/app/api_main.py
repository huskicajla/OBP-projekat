from fastapi import FastAPI, Query
import uvicorn
from .db import get_conn
from . import sqltexts as q
import pyodbc
import time

app = FastAPI(title="OBP 3-tier API")

def exec_nonquery(cur: pyodbc.Cursor, sql: str, params: tuple=()):
    cur.execute(sql, params)

@app.on_event("startup")
def startup():
    conn = get_conn()
    cur = conn.cursor()
    exec_nonquery(cur, q.CREATE_BENCH_TABLE)
    conn.commit()
    conn.close()

@app.post("/index/create")
def index_create():
    conn = get_conn()
    cur = conn.cursor()
    exec_nonquery(cur, q.DROP_INDEX_IF_EXISTS)
    exec_nonquery(cur, q.CREATE_INDEX)
    conn.commit()
    conn.close()
    return {"ok": True, "index": "IX_Posts_CreationDate"}

@app.post("/index/drop")
def index_drop():
    conn = get_conn()
    cur = conn.cursor()
    exec_nonquery(cur, q.DROP_INDEX_IF_EXISTS)
    conn.commit()
    conn.close()
    return {"ok": True}

@app.post("/insert")
def insert(n: int = Query(100, ge=1, le=10000)):
    conn = get_conn()
    cur = conn.cursor()
    exec_nonquery(cur, q.TRUNC_BENCH)
    t0 = time.perf_counter()
    exec_nonquery(cur, q.INSERT_SET_BASED, (n,))
    conn.commit()
    ms = (time.perf_counter() - t0) * 1000
    cnt = cur.execute(q.COUNT_BENCH).fetchone()[0]
    conn.close()
    return {"elapsed_ms": round(ms,3), "rows": int(cnt)}

@app.get("/select")
def select(sel_top: int = 200, dfrom: str = "2012-01-01", dto: str = "2014-01-01"):
    conn = get_conn()
    cur = conn.cursor()
    t0 = time.perf_counter()
    rows = cur.execute(q.SELECT_BY_DATE, (dfrom, dto, sel_top)).fetchall()
    ms = (time.perf_counter() - t0) * 1000
    conn.close()
    return {"elapsed_ms": round(ms,3), "rows": len(rows)}

@app.post("/update")
def update(k: int = 50):
    conn = get_conn()
    cur = conn.cursor()
    t0 = time.perf_counter()
    cur.execute(q.UPDATE_ON_BENCH, (k,))
    conn.commit()
    ms = (time.perf_counter() - t0) * 1000
    rc = cur.rowcount if cur.rowcount is not None else -1
    conn.close()
    return {"elapsed_ms": round(ms,3), "rows": rc}

@app.post("/delete")
def delete():
    conn = get_conn()
    cur = conn.cursor()
    t0 = time.perf_counter()
    cur.execute(q.DELETE_ON_BENCH)
    conn.commit()
    ms = (time.perf_counter() - t0) * 1000
    rc = cur.rowcount if cur.rowcount is not None else -1
    exec_nonquery(cur, q.TRUNC_BENCH)
    conn.close()
    return {"elapsed_ms": round(ms,3), "rows": rc}

if __name__ == "__main__":
    uvicorn.run("app.api_main:app", host="127.0.0.1", port=8000, reload=False)
