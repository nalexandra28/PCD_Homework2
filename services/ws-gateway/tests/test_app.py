import json

from starlette.testclient import TestClient

from ws_gateway.app import _map_notification_to_action


def test_healthz(client: TestClient) -> None:
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_map_notification() -> None:
    a = _map_notification_to_action(
        {
            "type": "movie_viewed",
            "movieId": "m1",
            "movieTitle": "T1",
            "at": "2026-01-01T00:00:00.000Z",
        }
    )
    assert a["type"] == "movie_viewed"
    assert a["movieId"] == "m1"


def test_map_notification_analytics_outbound() -> None:
    a = _map_notification_to_action(
        {
            "event": "movie_viewed",
            "data": {"movieId": "m1", "movieTitle": "T1"},
            "timestamp": "2026-01-01T00:00:00.000Z",
        }
    )
    assert a["type"] == "movie_viewed"
    assert a["movieId"] == "m1"
    assert a["movieTitle"] == "T1"
    assert "2026-01-01" in a["at"]


def test_websocket_welcome_and_snapshot(client: TestClient, demo_token: str) -> None:
    with client.websocket_connect(f"/ws?token={demo_token}") as w:
        m1 = json.loads(w.receive_text())
        m2 = json.loads(w.receive_text())
    assert m1.get("type") == "welcome"
    assert m2.get("type") == "stats.snapshot"
    assert "connectedClients" in m2
    assert "recentActions" in m2
    assert "popularMovies" in m2
