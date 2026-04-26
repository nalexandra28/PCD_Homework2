import pytest
from starlette.testclient import TestClient

from ws_gateway.app import create_app
from ws_gateway.registry import reset_connected_clients_for_tests


@pytest.fixture(autouse=True)
def _test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DISABLE_STATS_TIMER", "1")
    monkeypatch.setenv("GCP_PROJECT_ID", "")
    monkeypatch.setenv("EVENT_NOTIFICATIONS_SUBSCRIPTION", "")
    reset_connected_clients_for_tests()
    yield
    reset_connected_clients_for_tests()


@pytest.fixture
def demo_token() -> str:
    return "integration-test-token"


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, demo_token: str) -> TestClient:
    monkeypatch.setenv("WS_GATEWAY_DEMO_TOKEN", demo_token)
    with TestClient(create_app()) as c:
        yield c
