from __future__ import annotations

import asyncio
import json
import logging
import threading
from typing import Any, Awaitable, Callable, Optional

from google.cloud import pubsub_v1

logger = logging.getLogger("ws_gateway.pubsub_bridge")


class PubSubPullBridge:
    def __init__(
        self,
        *,
        project_id: str,
        subscription_id: str,
        loop: asyncio.AbstractEventLoop,
        on_message: Callable[[dict[str, Any]], Awaitable[None]],
    ) -> None:
        self._project_id = project_id
        self._subscription_id = subscription_id
        self._loop = loop
        self._on_message = on_message
        self._subscriber: Optional[pubsub_v1.SubscriberClient] = None
        self._streaming = None
        self._lock = threading.Lock()

    def start(self) -> None:
        with self._lock:
            if self._subscriber is not None:
                return
            self._subscriber = pubsub_v1.SubscriberClient()
        sub_path = self._subscriber.subscription_path(
            self._project_id, self._subscription_id
        )

        def callback(message: Any) -> None:
            try:
                data = json.loads(message.data.decode("utf-8"))
            except (UnicodeError, json.JSONDecodeError) as e:
                logger.warning("dropping non-JSON pubsub message: %s", e)
                try:
                    message.ack()
                except Exception:
                    pass
                return
            try:
                message.ack()
            except Exception:
                logger.debug("ack failed", exc_info=True)
                return

            def _done(f: asyncio.Future[Any]) -> None:
                try:
                    f.result()
                except Exception:
                    logger.debug("on_message failed", exc_info=True)

            fut = asyncio.run_coroutine_threadsafe(
                self._on_message(data), self._loop
            )
            fut.add_done_callback(_done)

        self._streaming = self._subscriber.subscribe(sub_path, callback=callback)
        logger.info("pubsub pull started", extra={"subscription": sub_path})

    def close(self) -> None:
        with self._lock:
            s = self._streaming
            sub = self._subscriber
            self._streaming = None
            self._subscriber = None
        if s is not None:
            s.cancel()
        if sub is not None:
            sub.close()
