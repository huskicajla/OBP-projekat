import argparse, csv, os, time, requests
API = "http://127.0.0.1:8000"
REPORTS = os.path.join(os.path.dirname(__file__), "..", "reports")
os.makedirs(REPORTS, exist_ok=True)
CSV_PATH = os.path.join(REPORTS, "results_3tier_h3.csv")

def call(method, path, **params):
    url = f"{API}{path}"; t0 = time.perf_counter()
    r = getattr(requests, method.lower())(url, params=params if method=="GET" else None, timeout=300)
    r.raise_for_status(); ms = (time.perf_counter()-t0)*1000.0
    return r.json(), ms

def write(row):
    new = not os.path.exists(CSV_PATH)
    with open(CSV_PATH,"a",newline="",encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=row.keys())
        if new: w.writeheader(); w.writerow(row)
        else: w.writerow(row)

def run_round(with_index, param_mode, pool_state, n, sel_top, dfrom, dto, upd_k, it):
    js,_ = call("POST","/insert", n=n)
    write({"arch":"3-tier","with_index":with_index,"pool":pool_state,"param_mode":param_mode,
           "crud":"INSERT","iter":it,"elapsed_ms":js["elapsed_ms"],"rows":js["rows"]})
    js,_ = call("GET","/select", sel_top=sel_top, dfrom=dfrom, dto=dto, param=param_mode)
    write({"arch":"3-tier","with_index":with_index,"pool":pool_state,"param_mode":param_mode,
           "crud":"SELECT","iter":it,"elapsed_ms":js["elapsed_ms"],"rows":js["rows"]})
    js,_ = call("POST","/update", k=upd_k)
    write({"arch":"3-tier","with_index":with_index,"pool":pool_state,"param_mode":param_mode,
           "crud":"UPDATE","iter":it,"elapsed_ms":js["elapsed_ms"],"rows":js["rows"]})
    js,_ = call("POST","/delete")
    write({"arch":"3-tier","with_index":with_index,"pool":pool_state,"param_mode":param_mode,
           "crud":"DELETE","iter":it,"elapsed_ms":js["elapsed_ms"],"rows":js["rows"]})

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

    if args.with_index: call("POST","/index/create")
    else:               call("POST","/index/drop")
    call("POST", f"/pool/{args.pool}")

    for it in range(1, args.iters+1):
        run_round(args.with_index, args.param, args.pool.upper(), args.n, args.sel_top, args.dfrom, args.dto, args.update_k, it)
    print("OK →", CSV_PATH)

if __name__ == "__main__":
    main()
