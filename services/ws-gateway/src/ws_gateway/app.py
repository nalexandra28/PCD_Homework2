from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
import random
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, AsyncIterator

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route, WebSocketRoute
from starlette.websockets import WebSocket, WebSocketDisconnect

from ws_gateway.auth import get_expected_demo_token, is_valid_demo_token_value
from ws_gateway.logutil import configure_logging
from ws_gateway.registry import (
    broadcast_text,
    get_connected_clients,
    register_client_connected,
    register_client_disconnected,
)
from ws_gateway.stats_state import StatsState

logger = logging.getLogger("ws_gateway.app")

WELCOME_PAYLOAD = {
    "type": "welcome",
    "message": "Connected to ws-gateway.",
}

_APP_SINGLETON: Starlette | None = None


def _get_starlette_app(websocket: WebSocket) -> Starlette:
    wapp = getattr(websocket, "app", None) or websocket.scope.get("app") or _APP_SINGLETON
    if wapp is None or not isinstance(wapp, Starlette):
        raise RuntimeError("WebSocket is missing Starlette app")
    return wapp


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _map_notification_to_action(data: dict[str, Any]) -> dict[str, Any]:
    # analytics-function publishes: { "event", "data": { movieId, movieTitle }, "timestamp" }
    # Optional flat form: { "type", "movieId", "movieTitle", "at" }
    nested = data.get("data")
    if isinstance(nested, dict):
        mid = str(nested.get("movieId", "") or "")
        mtitle = str(nested.get("movieTitle", "") or "")
    else:
        mid = str(data.get("movieId", "") or "")
        mtitle = str(data.get("movieTitle", "") or "")
    t = str(
        data.get("type")
        or data.get("event")
        or "unknown"
    )
    at_raw = data.get("at") or data.get("timestamp")
    at = str(at_raw) if at_raw is not None else _utcnow_iso()
    return {
        "type": t,
        "movieId": mid,
        "movieTitle": mtitle,
        "at": at,
    }


def _json_compact(obj: object) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=False)


async def _build_snapshot_str(stats: StatsState) -> str:
    recent, popular = await stats.get_lists()
    body = {
        "type": "stats.snapshot",
        "ts": _utcnow_iso(),
        "connectedClients": get_connected_clients(),
        "recentActions": recent,
        "popularMovies": popular,
    }
    return _json_compact(body)


@asynccontextmanager
async def lifespan(app: Starlette) -> AsyncIterator[None]:
    from ws_gateway import firestore_query

    app.state.stats = StatsState()
    stats: StatsState = app.state.stats

    async def broadcast() -> None:
        payload = await _build_snapshot_str(stats)
        await broadcast_text(payload)

    async def on_pubsub_data(data: dict[str, Any]) -> None:
        item = _map_notification_to_action(data)
        source_id = str(data.get("sourceEventId", "")) or None
        if not await stats.append_recent(item, source_id):
            return
        await broadcast()

    project = (os.environ.get("GCP_PROJECT_ID", "") or "").strip()
    subscription = (os.environ.get("EVENT_NOTIFICATIONS_SUBSCRIPTION", "") or "").strip()
    loop = asyncio.get_running_loop()
    bridge = None
    if project and subscription:
        from ws_gateway.pubsub_bridge import PubSubPullBridge

        bridge = PubSubPullBridge(
            project_id=project,
            subscription_id=subscription,
            loop=loop,
            on_message=on_pubsub_data,
        )
        bridge.start()
    else:
        logger.info(
            "pubsub not enabled (set GCP_PROJECT_ID and EVENT_NOTIFICATIONS_SUBSCRIPTION to subscribe)",
        )

    async def timer_loop() -> None:
        base = float(os.environ.get("STATS_TIMER_INTERVAL_SEC", "10"))
        while True:
            await asyncio.sleep(base * random.uniform(0.95, 1.05))
            try:
                popular = await asyncio.to_thread(
                    firestore_query.fetch_popular_movies_last_hour
                )
                await stats.set_popular(popular)
            except Exception:
                logger.exception("popular firestore read failed")
            try:
                await broadcast()
            except Exception:
                logger.exception("broadcast after timer failed")

    timer_task: asyncio.Task[None] | None = None
    if os.environ.get("DISABLE_STATS_TIMER", "").lower() not in (
        "1",
        "true",
        "yes",
    ):
        timer_task = asyncio.create_task(timer_loop(), name="stats-timer")
    with contextlib.suppress(Exception):
        initial = await asyncio.to_thread(
            firestore_query.fetch_popular_movies_last_hour
        )
        await stats.set_popular(initial)
    yield
    if timer_task is not None:
        timer_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await timer_task
    if bridge is not None:
        bridge.close()


async def healthz(_request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"}, status_code=200)


async def websocket_endpoint(websocket: WebSocket) -> None:
    expected = get_expected_demo_token()
    if not is_valid_demo_token_value(websocket.query_params.get("token"), expected):
        logger.warning(
            "WebSocket upgrade rejected",
            extra={
                "event": "ws_upgrade_rejected",
                "path": "/ws",
                "reason": "unauthorized",
                "connectedClients": get_connected_clients(),
            },
        )
        await websocket.send_denial_response(
            JSONResponse({"error": "Unauthorized"}, status_code=401)
        )
        return
    app = _get_starlette_app(websocket)
    stats: StatsState = app.state.stats
    await websocket.accept()
    register_client_connected(websocket)
    logger.info(
        "WebSocket client connected",
        extra={
            "event": "ws_connected",
            "path": "/ws",
            "connectedClients": get_connected_clients(),
        },
    )
    try:
        await websocket.send_text(_json_compact(WELCOME_PAYLOAD))
        with contextlib.suppress(Exception):
            await websocket.send_text(await _build_snapshot_str(stats))
        while True:
            await websocket.receive()
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.error(
            "WebSocket error",
            extra={"event": "ws_socket_error", "connectedClients": get_connected_clients()},
            exc_info=True,
        )
    finally:
        register_client_disconnected(websocket)
        logger.info(
            "WebSocket client disconnected",
            extra={
                "event": "ws_disconnected",
                "path": "/ws",
                "connectedClients": get_connected_clients(),
            },
        )


def create_app() -> Starlette:
    configure_logging(os.environ.get("LOG_LEVEL"))
    global _APP_SINGLETON
    app = Starlette(
        debug=os.environ.get("DEBUG", "").lower() in ("1", "true", "yes"),
        routes=[
            Route("/healthz", endpoint=healthz, methods=["GET"]),
            WebSocketRoute("/ws", endpoint=websocket_endpoint),
        ],
        lifespan=lifespan,
    )
    _APP_SINGLETON = app
    return app
