#!/usr/bin/env python3
import csv
import json
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from statistics import mean
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

_TOOLS = Path(__file__).resolve().parents[1]
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from load_config import resolve_gcp_project_region

POLL_INTERVAL_SEC = 1.0
POLL_MAX_ATTEMPTS = 20
PART1_RUNS = 5
BURST_N = 100
BURST_SLEEP_SEC = 5.0
BURST_CHECKS = 12
TOPIC_DEFAULT = "movie-events"

CSV_FIELDS = [
    "phase",
    "run_or_sample",
    "delay_s",
    "attempts",
    "ok",
    "burst_sample",
    "t_elapsed_s",
    "view_count",
    "publishes_done",
    "publish_target",
]

REST_QUERY = (
    "https://firestore.googleapis.com/v1/projects/{p}/databases/(default)/documents:runQuery"
)

_gc = shutil.which("gcloud")
_tok = ""
_tok_at = 0.0


def gcloud():
    if not _gc:
        raise RuntimeError("gcloud not on PATH")
    return _gc


def access_token():
    global _tok, _tok_at
    if _tok and time.time() - _tok_at < 50:
        return _tok
    r = subprocess.run(
        [gcloud(), "auth", "print-access-token"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if r.returncode != 0:
        raise RuntimeError(
            "No access token (run `gcloud auth login`). "
            + (r.stderr or r.stdout or "").strip()
        )
    _tok = (r.stdout or "").strip()
    _tok_at = time.time()
    return _tok


def firestore_count(project, movie_id, limit):
    url = REST_QUERY.format(p=project)
    body = json.dumps(
        {
            "structuredQuery": {
                "from": [{"collectionId": "movie-stats"}],
                "where": {
                    "fieldFilter": {
                        "field": {"fieldPath": "movieId"},
                        "op": "EQUAL",
                        "value": {"stringValue": movie_id},
                    }
                },
                "limit": limit,
            }
        }
    ).encode()
    req = Request(
        url,
        data=body,
        method="POST",
        headers={"Authorization": f"Bearer {access_token()}", "Content-Type": "application/json"},
    )
    try:
        raw = json.loads(urlopen(req, timeout=120).read().decode())
    except HTTPError as e:
        tail = e.read().decode(errors="replace")[:400] if e.fp else ""
        raise RuntimeError(f"Firestore HTTP {e.code}: {tail}") from e
    except URLError as e:
        raise RuntimeError(str(e)) from e
    if not isinstance(raw, list):
        return 0
    return sum(1 for x in raw if x.get("document"))


def publish(project, topic, movie_id, title):
    msg = json.dumps(
        {"event": "movie_viewed", "data": {"movieId": movie_id, "movieTitle": title}},
        separators=(",", ":"),
    )
    r = subprocess.run(
        [gcloud(), "pubsub", "topics", "publish", topic, "--message", msg, "--project", project],
        capture_output=True,
        text=True,
        timeout=180,
    )
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout or "").strip())


def write_csv(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS, restval="")
        w.writeheader()
        for row in rows:
            w.writerow(row)


def part1(project, topic):
    rows = []
    delays = []
    for run in range(1, PART1_RUNS + 1):
        mid = f"consistency_run{run}_{int(time.time())}"
        publish(project, topic, mid, f"Consistency test run {run}")
        t0 = time.perf_counter()
        hit = False
        for attempt in range(1, POLL_MAX_ATTEMPTS + 1):
            if firestore_count(project, mid, 1) > 0:
                sec = time.perf_counter() - t0
                delays.append(sec)
                rows.append(
                    {
                        "phase": "convergence",
                        "run_or_sample": run,
                        "delay_s": f"{sec:.4f}",
                        "attempts": attempt,
                        "ok": 1,
                    }
                )
                print(f"run {run}: {sec:.2f}s (attempt {attempt})", flush=True)
                hit = True
                break
            time.sleep(POLL_INTERVAL_SEC)
        if not hit:
            rows.append(
                {
                    "phase": "convergence",
                    "run_or_sample": run,
                    "attempts": POLL_MAX_ATTEMPTS,
                    "ok": 0,
                }
            )
            print(f"run {run}: timeout after {POLL_MAX_ATTEMPTS}s", flush=True)

    print("convergence_delays_s:", [round(x, 3) for x in delays], flush=True)
    if delays:
        m = mean(delays)
        print("mean_delay_s:", round(m, 3), flush=True)
        rows.append({"phase": "summary", "run_or_sample": "mean_delay_s", "delay_s": f"{m:.4f}"})
    return rows


def part2(project, topic):
    mid = f"burst_test_{int(time.time())}"
    rows = []

    def pub():
        publish(project, topic, mid, "Burst test")

    futs = []
    with ThreadPoolExecutor(max_workers=min(32, BURST_N)) as pool:
        for _ in range(BURST_N):
            futs.append(pool.submit(pub))
        for k in range(1, BURST_CHECKS + 1):
            time.sleep(BURST_SLEEP_SEC)
            done = sum(1 for f in futs if f.done())
            n = firestore_count(project, mid, 500)
            elapsed = k * BURST_SLEEP_SEC
            rows.append(
                {
                    "phase": "burst",
                    "burst_sample": k,
                    "t_elapsed_s": f"{elapsed:.1f}",
                    "view_count": n,
                    "publishes_done": done,
                    "publish_target": BURST_N,
                }
            )
            print(f"T+{elapsed:.0f}s viewCount={n} publishes_done={done}/{BURST_N}", flush=True)
    for f in futs:
        f.result()

    final = firestore_count(project, mid, 500)
    rows.append({"phase": "summary", "run_or_sample": "final_viewCount", "view_count": final})
    print("final_viewCount:", final, flush=True)
    return rows


def main():
    try:
        project, _ = resolve_gcp_project_region()
        access_token()
    except Exception as e:
        print(e, file=sys.stderr)
        sys.exit(2)

    topic = (os.environ.get("PUBSUB_TOPIC_MOVIE_EVENTS") or TOPIC_DEFAULT).strip()
    rows = part1(project, topic) + part2(project, topic)

    stamp = time.strftime("%Y%m%d-%H%M%S")
    root = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "metrics", "runs")
    path = os.path.join(root, f"consistency-{stamp}.csv")
    write_csv(path, rows)
    print("csv:", path, flush=True)


if __name__ == "__main__":
    main()
