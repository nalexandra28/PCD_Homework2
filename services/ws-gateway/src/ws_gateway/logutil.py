import json
import logging
import sys


def configure_logging(level: str | None) -> None:
    lvl = getattr(logging, (level or "INFO").upper(), logging.INFO)
    root = logging.getLogger()
    root.setLevel(lvl)
    h = logging.StreamHandler(sys.stdout)

    class Fmt(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            return (
                json.dumps(
                    {
                        "message": record.getMessage(),
                        "level": record.levelname,
                        "service": "ws-gateway",
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

    h.setFormatter(Fmt())
    root.handlers = [h]
