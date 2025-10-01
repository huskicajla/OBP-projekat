import argparse
import csv
import os
import time
from statistics import median
import pyodbc

from .db import get_conn
from . import sqltexts as q


REPORTS = os.path.join(os.path.dirname(__file__), "..", "reports")
os.makedirs(REPORTS, exist_ok=True)
RAW_CSV = os.path.join(REPORTS, "results_raw.csv")

def exec_nonquery(cur: pyodbc.Cursor, sql: str, params: tuple = ()):
    cur.execute(sql, params)

def fetch_all(cur: pyodbc.Cursor, sql: str, params: tuple = ()):
    cur.execute(sql, params)
    return cur.fetchall()

def measure(fn):
    t0 = time.perf_counter()
    out = fn()
    ms = (time.perf_counter() - t0) * 1000.0
    return ms, out

def ensure_bench(cur):
    exec_nonquery(cur, q.CREATE_BENCH_TABLE)

def drop_index_if_exists(cur):
    exec_nonquery(cur, q.DROP_INDEX_IF_EXISTS)

def create_index(cur):
    exec_nonquery(cur, q.CREATE_INDEX)

def truncate_bench(cur):
    exec_nonquery(cur, q.TRUNC_BENCH)

def do_insert(conn, n_rows: int) -> int:
    cur = conn.cursor()
    truncate_bench(cur)  
    exec_nonquery(cur, q.INSERT_SET_BASED, (n_rows,))
    cnt = fetch_all(cur, q.COUNT_BENCH)[0][0]
    conn.commit()
    return cnt

def do_select(conn, sel_top: int, dfrom: str, dto: str) -> int:
    cur = conn.cursor()
    rows = fetch_all(cur, q.SELECT_BY_DATE, (dfrom, dto, sel_top))
    
    return len(rows)

def do_update(conn, k: int) -> int:
    cur = conn.cursor()
    exec_nonquery(cur, q.UPDATE_ON_BENCH, (k,))
    affected = cur.rowcount if cur.rowcount is not None else -1
    conn.commit()
    return affected

def do_delete(conn) -> int:
    cur = conn.cursor()
    exec_nonquery(cur, q.DELETE_ON_BENCH)
    affected = cur.rowcount if cur.rowcount is not None else -1
    conn.commit()
    truncate_bench(cur)
    return affected

def write_raw(row: dict):
    file_exists = os.path.exists(RAW_CSV)
    with open(RAW_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=row.keys())
        if not file_exists:
            w.writeheader()
        w.writerow(row)

def run_round(conn, arch_label: str, with_index: bool, n_insert: int, sel_top: int, dfrom: str, dto: str, upd_k: int, iter_idx: int):
    # INSERT
    ms_ins, inserted = measure(lambda: do_insert(conn, n_insert))
    write_raw({
        "arch": arch_label, "with_index": with_index, "crud": "INSERT",
        "iter": iter_idx, "elapsed_ms": round(ms_ins, 3), "rows": inserted
    })

    # SELECT
    ms_sel, sel_rows = measure(lambda: do_select(conn, sel_top, dfrom, dto))
    write_raw({
        "arch": arch_label, "with_index": with_index, "crud": "SELECT",
        "iter": iter_idx, "elapsed_ms": round(ms_sel, 3), "rows": sel_rows
    })

    # UPDATE
    ms_upd, upd_rows = measure(lambda: do_update(conn, upd_k))
    write_raw({
        "arch": arch_label, "with_index": with_index, "crud": "UPDATE",
        "iter": iter_idx, "elapsed_ms": round(ms_upd, 3), "rows": upd_rows
    })

    # DELETE
    ms_del, del_rows = measure(lambda: do_delete(conn))
    write_raw({
        "arch": arch_label, "with_index": with_index, "crud": "DELETE",
        "iter": iter_idx, "elapsed_ms": round(ms_del, 3), "rows": del_rows
    })

def main():
    ap = argparse.ArgumentParser(description="OBP 2-tier CRUD benchmark")
    ap.add_argument("--iters", type=int, default=3, help="koliko puta ponoviti set CRUD-a")
    ap.add_argument("--n", type=int, default=100, help="koliko redova ubaciti u INSERT")
    ap.add_argument("--sel-top", type=int, default=200)
    ap.add_argument("--from", dest="dfrom", default="2012-01-01")
    ap.add_argument("--to", dest="dto", default="2014-01-01")
    ap.add_argument("--update-k", type=int, default=50)
    ap.add_argument("--with-index", action="store_true", help="ako je postavljeno, koristi indeks")
    args = ap.parse_args()

    conn = get_conn(autocommit=False)
    cur = conn.cursor()
    ensure_bench(cur)

    drop_index_if_exists(cur)
    if args.with_index:
        create_index(cur)
        conn.commit()

    arch = "2-tier"
    for it in range(1, args.iters + 1):
        run_round(conn, arch, args.with_index, args.n, args.sel_top, args.dfrom, args.dto, args.update_k, it)

    conn.close()
    print(f"Gotovo. Rezultati su u: {RAW_CSV}")

if __name__ == "__main__":
    main()
