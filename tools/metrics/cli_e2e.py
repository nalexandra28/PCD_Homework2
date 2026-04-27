#!/usr/bin/env python3
import csv
import json
import math
import os
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
from urllib.request import Request, urlopen

_TOOLS = Path(__file__).resolve().parents[1]
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from load_config import resolve_cloud_metrics_endpoints

import websocket

WS_RECV_TIMEOUT = 120
WAIT_ONE_GET_SEC = 120

WARMUP = 5
SAMPLES = 35


def build_ws_url(ws_url_raw: str, token: str) -> str:
    parsed = urlparse(ws_url_raw)
    query = parse_qs(parsed.query)
    query["token"] = [token]
    new_query = urlencode(query, doseq=True)
    return urlunparse(
        (parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment)
    )


def pct(sorted_ms, p):
    n = len(sorted_ms)
    if n == 0:
        return float("nan")
    k = max(0, min(n - 1, math.ceil(p / 100.0 * n) - 1))
    return sorted_ms[k]


def movie_ts(snap, mid):
    best = None
    for row in snap.get("recentActions") or []:
        if row.get("movieId") != mid:
            continue
        t = row.get("at") or ""
        if best is None or t > best:
            best = t
    for row in snap.get("popularMovies") or []:
        if row.get("movieId") != mid:
            continue
        t = row.get("timestamp") or ""
        if best is None or t > best:
            best = t
    return best


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

    mid = ep.movie_id
    auth = ep.ws_token.strip()
    base = ep.api_base.rstrip("/")
    ws_url = build_ws_url(ep.ws_url_raw, ep.ws_token)
    url = f"{base}/movies/{mid}"
    hdr = {"Accept": "application/json"}
    if auth:
        hdr["Authorization"] = f"Bearer {auth}"

    ws = websocket.WebSocket()
    try:
        ws.connect(ws_url, timeout=60)
    except (OSError, URLError) as e:
        print("WebSocket connect failed:", e, file=sys.stderr)
        sys.exit(2)

    last_snap_ts = ""
    for _ in range(2):
        ws.settimeout(60)
        raw = ws.recv()
        try:
            m = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if m.get("type") == "stats.snapshot" and m.get("ts"):
            last_snap_ts = m["ts"]

    rows = []
    total = WARMUP + SAMPLES
    for i in range(total):
        req = Request(url, headers=hdr, method="GET")
        with urlopen(req, timeout=60) as r:
            r.read()
        t_http = time.perf_counter()
        lat = None
        deadline = time.monotonic() + WAIT_ONE_GET_SEC
        while time.monotonic() < deadline:
            remain = min(float(WS_RECV_TIMEOUT), max(0.1, deadline - time.monotonic()))
            ws.settimeout(remain)
            try:
                raw = ws.recv()
            except websocket.WebSocketTimeoutException:
                break
            t_msg = time.perf_counter()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if msg.get("type") != "stats.snapshot":
                continue
            gts = msg.get("ts") or ""
            if not gts or gts <= last_snap_ts:
                continue
            if not movie_ts(msg, mid):
                continue
            last_snap_ts = gts
            lat = (t_msg - t_http) * 1000.0
            break
        if lat is None:
            print("timeout: no fresh snapshot for movie", mid, file=sys.stderr)
            sys.exit(1)
        rows.append((i, lat, i >= WARMUP))

    out_dir = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "metrics", "runs")
    os.makedirs(out_dir, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    path = os.path.join(out_dir, f"e2e-{stamp}.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["iteration", "latency_ms", "counted"])
        for i, lat, counted in rows:
            w.writerow([i, f"{lat:.3f}", counted])

    measured = [lat for (_, lat, c) in rows if c]
    measured.sort()
    print("raw:", path)
    print("warmup_excluded:", WARMUP, "counted:", len(measured))
    print(
        "p50_ms",
        pct(measured, 50),
        "p95_ms",
        pct(measured, 95),
        "min_ms",
        measured[0],
        "max_ms",
        measured[-1],
    )
    print("consistency_window_ms_typical=p50", "observed_max=max", sep=" ")


if __name__ == "__main__":
    main()
