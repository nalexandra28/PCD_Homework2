from __future__ import annotations

import logging

from starlette.websockets import WebSocket

logger = logging.getLogger("ws_gateway.registry")

_websockets: set[WebSocket] = set()


def get_connected_clients() -> int:
    return len(_websockets)


def register_client_connected(websocket: WebSocket) -> None:
    _websockets.add(websocket)


def register_client_disconnected(websocket: WebSocket) -> None:
    _websockets.discard(websocket)


def reset_connected_clients_for_tests() -> None:
    _websockets.clear()


async def broadcast_text(payload: str) -> None:
    if not _websockets:
        return
    to_remove: list[WebSocket] = []
    for ws in list(_websockets):
        try:
            await ws.send_text(payload)
        except Exception:
            logger.debug("broadcast: drop dead socket", exc_info=True)
            to_remove.append(ws)
    for ws in to_remove:
        _websockets.discard(ws)
