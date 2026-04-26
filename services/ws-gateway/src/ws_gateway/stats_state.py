from __future__ import annotations

import asyncio
import os
from collections import deque
from typing import Any


def _recent_actions_max() -> int:
    try:
        n = int(os.environ.get("RECENT_ACTIONS_MAX", "15"))
    except ValueError:
        return 15
    return max(1, min(n, 50))


class StatsState:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        cap = _recent_actions_max()
        self.recent_actions: deque[dict[str, Any]] = deque(maxlen=cap)
        self.popular_movies: list[dict[str, Any]] = []
        self._seen_event_ids: deque[str] = deque(maxlen=max(100, cap * 3))

    async def append_recent(
        self,
        item: dict[str, Any],
        source_event_id: str | None,
    ) -> bool:
        async with self._lock:
            if source_event_id and source_event_id in self._seen_event_ids:
                return False
            if source_event_id:
                self._seen_event_ids.append(source_event_id)
            self.recent_actions.append(item)
        return True

    async def set_popular(self, rows: list[dict[str, Any]]) -> None:
        async with self._lock:
            self.popular_movies = list(rows)

    async def get_lists(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        async with self._lock:
            recent = list(reversed(self.recent_actions))
            return (recent, list(self.popular_movies))
