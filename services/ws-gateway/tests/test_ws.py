import json

import pytest
from starlette.testclient import TestClient, WebSocketDenialResponse

from ws_gateway.registry import get_connected_clients


def test_ws_rejects_without_token(client: TestClient) -> None:
    with pytest.raises(WebSocketDenialResponse) as ctx:
        with client.websocket_connect("/ws"):
            pass
    assert ctx.value.status_code == 401


def test_ws_rejects_wrong_token(client: TestClient) -> None:
    with pytest.raises(WebSocketDenialResponse) as ctx:
        with client.websocket_connect("/ws?token=wrong"):
            pass
    assert ctx.value.status_code == 401


def test_ws_accepts_valid_token_and_tracks_count(client: TestClient, demo_token: str) -> None:
    assert get_connected_clients() == 0
    path = f"/ws?token={demo_token}"
    with client.websocket_connect(path) as ws:
        assert get_connected_clients() == 1
        msg = ws.receive_text()
        payload = json.loads(msg)
        assert payload["type"] == "welcome"
    assert get_connected_clients() == 0
