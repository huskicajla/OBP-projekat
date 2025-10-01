import argparse, threading, time, statistics, requests, csv, os
API = "http://127.0.0.1:8000"
REPORTS = os.path.join(os.path.dirname(__file__), "..", "reports")
os.makedirs(REPORTS, exist_ok=True)
CSV_PATH = os.path.join(REPORTS, "results_3tier_concurrency.csv")

def call(method, path, **params):
    url = f"{API}{path}"
    r = getattr(requests, method.lower())(url, params=params if method=="GET" else None, timeout=300)
    r.raise_for_status(); return r.json()

def worker(rounds, params, out):
    for _ in range(rounds):
        t0 = time.perf_counter()
        r = requests.get(f"{API}/select", params=params, timeout=300)
        r.raise_for_status()
        out.append((time.perf_counter()-t0)*1000.0)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threads", type=int, default=10)
    ap.add_argument("--rounds", type=int, default=5)
    ap.add_argument("--sel-top", type=int, default=200)
    ap.add_argument("--from", dest="dfrom", default="2012-01-01")
    ap.add_argument("--to", dest="dto", default="2014-01-01")
    ap.add_argument("--with-index", action="store_true")
    ap.add_argument("--pool", choices=["on","off"], default="on")
    ap.add_argument("--param", choices=["on","off"], default="on")
    args = ap.parse_args()

    if args.with_index: call("POST","/index/create")
    else:               call("POST","/index/drop")
    call("POST", f"/pool/{args.pool}")

    params = dict(sel_top=args.sel_top, dfrom=args.dfrom, dto=args.dto, param=args.param)
    times=[]; threads=[threading.Thread(target=worker, args=(args.rounds, params, times)) for _ in range(args.threads)]
    [t.start() for t in threads]; [t.join() for t in threads]

    p50 = statistics.median(times)
    p95 = sorted(times)[int(0.95*len(times))-1] if times else None
    row = dict(arch="3-tier", with_index=args.with_index, pool=args.pool.upper(),
               param_mode=args.param, concurrency=args.threads, rounds=args.rounds,
               p50_ms=round(p50,3), p95_ms=round(p95,3) if p95 else None)

    new = not os.path.exists(CSV_PATH)
    with open(CSV_PATH,"a",newline="",encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=row.keys())
        if new: w.writeheader(); w.writerow(row)
        else: w.writerow(row)
    print("OK →", CSV_PATH, "| p50=", round(p50,3), "ms ; p95=", round(p95,3) if p95 else None)

if __name__ == "__main__":
    main()
