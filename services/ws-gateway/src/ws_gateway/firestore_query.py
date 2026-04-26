from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

from google.cloud import firestore


def _get_database_id() -> str:
    v = (os.environ.get("FIRESTORE_DATABASE_ID", "") or "").strip()
    if not v or v == "default":
        return "(default)"
    return v


def _client() -> firestore.Client:
    project = (os.environ.get("GCP_PROJECT_ID") or "").strip() or None
    return firestore.Client(project=project, database=_get_database_id())


def fetch_popular_movies_last_hour() -> list[dict[str, Any]]:
    hours = int(os.environ.get("POPULAR_WINDOW_HOURS", "1"))
    limit = int(os.environ.get("POPULAR_LIMIT", "10"))
    col = _client().collection("movie-stats")
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).replace(
        microsecond=0
    )
    floor = cutoff.isoformat().replace("+00:00", "Z")
    q = col.where("timestamp", ">=", floor)
    by_movie: dict[str, dict[str, Any]] = {}
    for doc in q.stream():
        d = doc.to_dict() or {}
        mid = str(d.get("movieId", doc.id))
        title = str(d.get("movieTitle", "Unknown"))
        ts = d.get("timestamp")
        if mid not in by_movie:
            by_movie[mid] = {
                "movieId": mid,
                "movieTitle": title,
                "viewCount": 0,
                "timestamp": ts,
            }
        else:
            if not by_movie[mid].get("movieTitle") or by_movie[mid]["movieTitle"] == "Unknown":
                by_movie[mid]["movieTitle"] = title
        row = by_movie[mid]
        row["viewCount"] = int(row.get("viewCount", 0)) + 1
        old_ts = row.get("timestamp")
        if ts and (not old_ts or str(ts) > str(old_ts)):
            row["timestamp"] = ts
    out = sorted(
        by_movie.values(),
        key=lambda r: (int(r.get("viewCount", 0)), str(r.get("timestamp") or "")),
        reverse=True,
    )[:limit]
    return [dict(x) for x in out]
