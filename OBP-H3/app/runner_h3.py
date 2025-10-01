import argparse, csv, os, time, pyodbc
from .db import get_conn
from . import sqltexts as q

def measure(fn):
    t0 = time.perf_counter(); out = fn()
    return (time.perf_counter()-t0)*1000.0, out

def do_insert(conn, n):
    cur = conn.cursor(); cur.execute(q.TRUNC_BENCH)
    t0 = time.perf_counter()
    for _ in range(n):
        cur.execute("""
            INSERT INTO dbo.Posts (PostTypeId, Body, CreationDate, LastActivityDate, Score, ViewCount)
            OUTPUT INSERTED.Id INTO dbo._BenchPosts(PostId)
            VALUES (1, REPLICATE(N'Q',400), SYSDATETIME(), SYSDATETIME(), 0, 0);
        """)
    conn.commit()
    ms = (time.perf_counter()-t0)*1000.0
    cnt = cur.execute(q.COUNT_BENCH).fetchone()[0]
    return ms, cnt

def do_select(conn, sel_top, dfrom, dto, param_on=True):
    cur = conn.cursor()
    if param_on:
        t0 = time.perf_counter()
        rows = cur.execute(q.SELECT_BY_DATE, (sel_top, dfrom, dto)).fetchall()
    else:
        sql = f"""
        SELECT TOP ({sel_top}) p.Id, p.CreationDate, p.Score
        FROM dbo.Posts AS p
        WHERE p.CreationDate BETWEEN '{dfrom}' AND '{dto}'
        ORDER BY p.CreationDate DESC;
        """
        t0 = time.perf_counter()
        rows = cur.execute(sql).fetchall()
    ms = (time.perf_counter()-t0)*1000.0
    return ms, len(rows)

def do_update(conn, k):
    cur = conn.cursor(); t0 = time.perf_counter()
    cur.execute(q.UPDATE_ON_BENCH, (k,)); conn.commit()
    ms = (time.perf_counter()-t0)*1000.0
    rc = cur.rowcount if cur.rowcount is not None else -1
    return ms, rc

def do_delete(conn):
    cur = conn.cursor(); t0 = time.perf_counter()
    cur.execute(q.DELETE_ON_BENCH); conn.commit()
    ms = (time.perf_counter()-t0)*1000.0
    rc = cur.rowcount if cur.rowcount is not None else -1
    cur.execute(q.TRUNC_BENCH); conn.commit()
    return ms, rc

def write_row(path, row):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    new = not os.path.exists(path)
    with open(path,"a",newline="",encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=row.keys())
        if new: w.writeheader()
        w.writerow(row)

def run_round(conn, arch, with_index, n, sel_top, dfrom, dto, upd_k, it, pool_state, param_mode, out_csv):
    ms, rows = measure(lambda: do_insert(conn, n))
    write_row(out_csv, dict(arch=arch, with_index=with_index, pool=pool_state, param_mode=param_mode,
                            crud="INSERT", iter=it, elapsed_ms=round(ms,3), rows=rows))
    ms, rows = measure(lambda: do_select(conn, sel_top, dfrom, dto, param_on=(param_mode=="on")))
    write_row(out_csv, dict(arch=arch, with_index=with_index, pool=pool_state, param_mode=param_mode,
                            crud="SELECT", iter=it, elapsed_ms=round(ms,3), rows=rows))
    ms, rows = measure(lambda: do_update(conn, upd_k))
    write_row(out_csv, dict(arch=arch, with_index=with_index, pool=pool_state, param_mode=param_mode,
                            crud="UPDATE", iter=it, elapsed_ms=round(ms,3), rows=rows))
    ms, rows = measure(lambda: do_delete(conn))
    write_row(out_csv, dict(arch=arch, with_index=with_index, pool=pool_state, param_mode=param_mode,
                            crud="DELETE", iter=it, elapsed_ms=round(ms,3), rows=rows))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iters", type=int, default=3)
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--sel-top", type=int, default=200)
    ap.add_argument("--from", dest="dfrom", default="2012-01-01")
    ap.add_argument("--to", dest="dto", default="2014-01-01")
    ap.add_argument("--update-k", type=int, default=50)
    ap.add_argument("--with-index", action="store_true")
    ap.add_argument("--pool", choices=["on","off"], default="on")
    ap.add_argument("--param", choices=["on","off"], default="on")
    args = ap.parse_args()

    pyodbc.pooling = (args.pool == "on")

    conn = get_conn()
    cur = conn.cursor(); cur.execute(q.CREATE_BENCH_TABLE)
    if args.with_index: cur.execute(q.DROP_INDEX_IF_EXISTS); cur.execute(q.CREATE_INDEX)
    else:               cur.execute(q.DROP_INDEX_IF_EXISTS)
    conn.commit()

    out_csv = os.path.join(os.path.dirname(__file__), "..", "reports", "results_2tier_h3.csv")
    arch = "2-tier"
    for it in range(1, args.iters+1):
        run_round(conn, arch, args.with_index, args.n, args.sel_top, args.dfrom, args.dto, args.update_k,
                  it, args.pool.upper(), args.param.lower(), out_csv)
    conn.close(); print("OK →", out_csv)

if __name__ == "__main__":
    main()
