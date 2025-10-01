from fastapi import FastAPI, Query
from queue import Queue
import time, uvicorn
from .db import get_conn
from . import sqltexts as q

app = FastAPI(title="OBP 3-tier API (H3)")
USE_POOL = True
POOL: Queue | None = None

def get_conn_from_pool():
    if not USE_POOL:
        return get_conn()
    return POOL.get()

def return_conn(conn):
    if not USE_POOL:
        conn.close(); return
    POOL.put(conn)

@app.on_event("startup")
def startup():
    global POOL
    POOL = Queue()
    for _ in range(5):
        POOL.put(get_conn())
    c = get_conn(); cur = c.cursor()
    cur.execute(q.CREATE_BENCH_TABLE); c.commit(); c.close()

@app.post("/pool/{state}")
def set_pool(state: str):
    global USE_POOL
    USE_POOL = (state.lower() == "on")
    return {"ok": True, "pool": "ON" if USE_POOL else "OFF"}

@app.post("/index/create")
def index_create():
    conn = get_conn_from_pool(); cur = conn.cursor()
    cur.execute(q.DROP_INDEX_IF_EXISTS); cur.execute(q.CREATE_INDEX)
    conn.commit(); return_conn(conn); return {"ok": True}

@app.post("/index/drop")
def index_drop():
    conn = get_conn_from_pool(); cur = conn.cursor()
    cur.execute(q.DROP_INDEX_IF_EXISTS); conn.commit()
    return_conn(conn); return {"ok": True}

@app.post("/insert")
def insert(n: int = Query(100, ge=1, le=10000)):
    conn = get_conn_from_pool(); cur = conn.cursor()
    cur.execute(q.TRUNC_BENCH)
    t0 = time.perf_counter()
    for _ in range(n):
        cur.execute("""
            INSERT INTO dbo.Posts (PostTypeId, Body, CreationDate, LastActivityDate, Score, ViewCount)
            OUTPUT INSERTED.Id INTO dbo._BenchPosts(PostId)
            VALUES (1, REPLICATE(N'Q',400), SYSDATETIME(), SYSDATETIME(), 0, 0);
        """)
    conn.commit(); ms = (time.perf_counter()-t0)*1000
    cnt = cur.execute(q.COUNT_BENCH).fetchone()[0]
    return_conn(conn); return {"elapsed_ms": round(ms,3), "rows": int(cnt)}

@app.get("/select")
def select(sel_top: int = 200, dfrom: str = "2012-01-01", dto: str = "2014-01-01", param: str = "on"):
    conn = get_conn_from_pool(); cur = conn.cursor()
    t0 = time.perf_counter()
    if param.lower() == "on":
        rows = cur.execute(q.SELECT_BY_DATE, (sel_top, dfrom, dto)).fetchall()
    else:
        sql = f"""
        SELECT TOP ({sel_top}) p.Id, p.CreationDate, p.Score
        FROM dbo.Posts AS p
        WHERE p.CreationDate BETWEEN '{dfrom}' AND '{dto}'
        ORDER BY p.CreationDate DESC;
        """
        rows = cur.execute(sql).fetchall()
    ms = (time.perf_counter()-t0)*1000
    return_conn(conn); return {"elapsed_ms": round(ms,3), "rows": len(rows)}

@app.post("/update")
def update(k: int = 50):
    conn = get_conn_from_pool(); cur = conn.cursor()
    t0 = time.perf_counter(); cur.execute(q.UPDATE_ON_BENCH, (k,)); conn.commit()
    ms = (time.perf_counter()-t0)*1000
    rc = cur.rowcount if cur.rowcount is not None else -1
    return_conn(conn); return {"elapsed_ms": round(ms,3), "rows": rc}

@app.post("/delete")
def delete():
    conn = get_conn_from_pool(); cur = conn.cursor()
    t0 = time.perf_counter(); cur.execute(q.DELETE_ON_BENCH); conn.commit()
    ms = (time.perf_counter()-t0)*1000
    rc = cur.rowcount if cur.rowcount is not None else -1
    cur.execute(q.TRUNC_BENCH); conn.commit()
    return_conn(conn); return {"elapsed_ms": round(ms,3), "rows": rc}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
