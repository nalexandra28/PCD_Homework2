import os


def get_expected_demo_token() -> str:
    return (os.environ.get("WS_GATEWAY_DEMO_TOKEN") or "").strip()


def is_valid_demo_token_value(value: str | None, expected: str) -> bool:
    if not expected or value is None:
        return False
    return value.strip() == expected
