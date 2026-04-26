from __future__ import annotations

from unittest import mock
from unittest.mock import MagicMock


@mock.patch("ws_gateway.firestore_query.firestore.Client")
def test_fetch_popular(m_cl: MagicMock) -> None:
    doc = MagicMock()
    doc.to_dict.return_value = {
        "movieId": "m1",
        "movieTitle": "T1",
        "timestamp": "s1",
    }
    where = m_cl.return_value.collection.return_value.where.return_value
    where.stream = MagicMock(return_value=iter([doc, doc]))

    from ws_gateway import firestore_query

    rows = firestore_query.fetch_popular_movies_last_hour()
    assert len(rows) == 1
    assert rows[0]["movieId"] == "m1"
    assert rows[0]["viewCount"] == 2
