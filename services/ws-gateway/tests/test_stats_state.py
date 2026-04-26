import asyncio

from ws_gateway.stats_state import StatsState


def test_dedupes() -> None:
    async def _r() -> None:
        s = StatsState()
        a = {
            "type": "movie_viewed",
            "movieId": "1",
            "movieTitle": "A",
            "at": "z",
        }
        assert await s.append_recent(a, "ev1") is True
        assert await s.append_recent(a, "ev1") is False
        l1, _l2 = await s.get_lists()
        assert len(l1) == 1
        assert l1[0]["movieId"] == "1"

    asyncio.run(_r())


def test_recent_newest_first() -> None:
    async def _r() -> None:
        s = StatsState()
        await s.append_recent(
            {"type": "movie_viewed", "movieId": "1", "movieTitle": "A", "at": "a1"},
            "e1",
        )
        await s.append_recent(
            {"type": "movie_viewed", "movieId": "2", "movieTitle": "B", "at": "a2"},
            "e2",
        )
        recent, _p = await s.get_lists()
        assert len(recent) == 2
        assert recent[0]["movieId"] == "2"
        assert recent[1]["movieId"] == "1"

    asyncio.run(_r())


def test_set_popular() -> None:
    async def _r() -> None:
        s = StatsState()
        await s.set_popular(
            [{"movieId": "a", "movieTitle": "b", "timestamp": "c"}]
        )
        _a, p = await s.get_lists()
        assert len(p) == 1

    asyncio.run(_r())
