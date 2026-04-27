#!/usr/bin/env python3
import csv
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

_TOOLS = Path(__file__).resolve().parents[1]
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from load_config import resolve_cloud_metrics_endpoints

STAGES = (1, 3, 5)
STAGE_SECONDS = 20


def get1(url, hdr):
    try:
        req = Request(url, headers=hdr, method="GET")
        with urlopen(req, timeout=45) as r:
            r.read()
            return r.getcode(), ""
    except HTTPError as e:
        return e.code, str(e)[:120]
    except URLError as e:
        return 0, str(e)[:120]
    except Exception as e:
        return 0, repr(e)[:120]


def main():
    try:
        ep = resolve_cloud_metrics_endpoints()
    except Exception as e:
        print(
            "Cloud endpoints resolution failed:",
            e,
            file=sys.stderr,
        )
        sys.exit(2)

    base = ep.api_base.rstrip("/")
    mid = ep.movie_id
    jwt = ep.ws_token.strip()

    url = f"{base}/movies/{mid}"
    hdr = {"Accept": "application/json"}
    if jwt:
        hdr["Authorization"] = f"Bearer {jwt}"

    rows, n = [], 0
    for si, w in enumerate(STAGES):
        t_end = time.time() + STAGE_SECONDS
        while time.time() < t_end:
            with ThreadPoolExecutor(max_workers=w) as ex:
                fs = [ex.submit(get1, url, hdr) for _ in range(w)]
                for f in as_completed(fs):
                    n += 1
                    code, err = f.result()
                    ok = 1 if code == 200 else 0
                    rows.append([time.time(), si, w, n, ok, code, err])

    d = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "metrics", "runs")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, time.strftime("load-http-%Y%m%d-%H%M%S.csv"))
    with open(p, "w", newline="") as f:
        cw = csv.writer(f)
        cw.writerow(["unix_ts", "stage", "workers", "attempt", "ok", "http_code", "err"])
        cw.writerows(rows)

    okc = sum(r[4] for r in rows)
    print("csv:", p)
    print("attempts", len(rows), "http_ok", okc, "http_err_ratio", round(1 - okc / len(rows), 4) if rows else 0)
    for si in range(len(STAGES)):
        sub = [r for r in rows if r[1] == si]
        if not sub:
            continue
        dt = sub[-1][0] - sub[0][0]
        print("stage", si, "workers", STAGES[si], "rps", round(len(sub) / max(dt, 1e-6), 2))


if __name__ == "__main__":
    main()
