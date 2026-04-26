import os

import uvicorn

from ws_gateway.app import create_app

app = create_app()


def run() -> None:
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8080"))
    uvicorn.run(
        "ws_gateway.main:app",
        host=host,
        port=port,
        factory=False,
        log_config=None,
        access_log=False,
    )


if __name__ == "__main__":
    run()
