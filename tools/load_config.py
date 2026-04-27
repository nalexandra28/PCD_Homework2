from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

_REPO_ROOT = Path(__file__).resolve().parents[1]
_ENV_PATH = _REPO_ROOT / ".env"

_FAST_LAZY_BEE_SERVICE = "fast-lazy-bee"
_WS_GATEWAY_SERVICE = "ws-gateway"
_METRICS_MOVIE_ID = "573a13a0f29313caabd041db"


def _require_after_dotenv(name: str) -> str:
    v = (os.environ.get(name) or "").strip()
    if not v:
        raise RuntimeError(f"Missing {name} in environment (set it in {_ENV_PATH} or export it)")
    return v


def _gcloud_run_service_url(service: str, project: str, region: str) -> str:
    gcloud = shutil.which("gcloud")
    if not gcloud:
        raise RuntimeError("gcloud CLI not found on PATH; install Google Cloud SDK to resolve Cloud Run URLs")
    r = subprocess.run(
        [
            gcloud,
            "run",
            "services",
            "describe",
            service,
            "--project",
            project,
            "--region",
            region,
            "--format",
            "value(status.url)",
        ],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    out = (r.stdout or "").strip()
    err = (r.stderr or "").strip()
    if r.returncode != 0 or not out:
        msg = err or out or f"exit {r.returncode}"
        raise RuntimeError(f"gcloud run services describe {service} failed: {msg}")
    return out


def _http_base_url_to_ws_path(http_url: str) -> str:
    u = http_url.strip().rstrip("/")
    if u.startswith("https://"):
        return "wss://" + u[len("https://") :] + "/ws"
    if u.startswith("http://"):
        return "ws://" + u[len("http://") :] + "/ws"
    raise RuntimeError(f"Unexpected Cloud Run URL scheme: {http_url!r}")


@dataclass(frozen=True)
class ResolvedMetricsEndpoints:
    api_base: str
    movie_id: str
    ws_url_raw: str
    ws_token: str
    authorization: str | None


def load_repo_dotenv() -> None:
    if not _ENV_PATH.is_file():
        return
    load_dotenv(_ENV_PATH, override=True)


def resolve_gcp_project_region() -> tuple[str, str]:
    if not _ENV_PATH.is_file():
        raise RuntimeError(f"Missing {_ENV_PATH} (copy from .env.example and fill values)")
    load_repo_dotenv()
    project = _require_after_dotenv("GCP_PROJECT_ID")
    region = _require_after_dotenv("GCP_REGION")
    return project, region


def resolve_cloud_metrics_endpoints() -> ResolvedMetricsEndpoints:
    if not _ENV_PATH.is_file():
        raise RuntimeError(f"Missing {_ENV_PATH} (copy from .env.example and fill values)")
    load_repo_dotenv()
    project = _require_after_dotenv("GCP_PROJECT_ID")
    region = _require_after_dotenv("GCP_REGION")
    token = _require_after_dotenv("WS_GATEWAY_DEMO_TOKEN")

    api_http = _gcloud_run_service_url(_FAST_LAZY_BEE_SERVICE, project, region)
    ws_http = _gcloud_run_service_url(_WS_GATEWAY_SERVICE, project, region)

    api_base = api_http.rstrip("/") + "/api/v1"
    ws_url_raw = _http_base_url_to_ws_path(ws_http)

    return ResolvedMetricsEndpoints(
        api_base=api_base,
        movie_id=_METRICS_MOVIE_ID,
        ws_url_raw=ws_url_raw,
        ws_token=token,
        authorization=None,
    )
