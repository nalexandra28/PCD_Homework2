import pytest

from ws_gateway.auth import is_valid_demo_token_value


@pytest.mark.parametrize(
    ("value", "secret", "expected"),
    [
        ("demo-secret-token", "demo-secret-token", True),
        ("  tok  ", "tok", True),
        ("other", "demo-secret-token", False),
        (None, "demo-secret-token", False),
        ("x", "", False),
    ],
)
def test_is_valid_demo_token_value(value: str | None, secret: str, expected: bool) -> None:
    assert is_valid_demo_token_value(value, secret) is expected
