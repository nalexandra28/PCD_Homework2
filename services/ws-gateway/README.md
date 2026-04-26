# WebSocket gateway

Python **Starlette** service: **GET /healthz** (no auth) and **WebSocket** **/ws** authenticated with query parameter `**token=<WS_GATEWAY_DEMO_TOKEN>`** (for example `wss://host/ws?token=...`). 

## WebSocket messages (JSON text)

**1. Welcome** (right after the upgrade):

```json
{ "type": "welcome", "message": "Connected to ws-gateway." }
```

**2. Stats snapshot** (right after welcome, and whenever Pub/Sub or the timer triggers a push):

```json
{
  "type": "stats.snapshot",
  "ts": "2026-04-25T12:00:00.000Z",
  "connectedClients": 0,
  "recentActions": [ { "type": "movie_viewed", "movieId": "…", "movieTitle": "…", "at": "…" } ],
  "popularMovies": [ { "movieId": "…", "movieTitle": "…", "timestamp": "…" } ]
}
```

- **connectedClients** — count for this process only (each Cloud Run replica has its own number).
- **recentActions** — at most **RECENT_ACTIONS_MAX** items, **newest first**; from **event-notifications** Pub/Sub, after your analytics pipeline processes **movie-events**.
- **popularMovies** — from Firestore **movie-stats**.

The gateway pulls from Pub/Sub and runs a timer to refresh **popularMovies** and broadcast.

## Environment


| Variable                                 | Notes                                                               |
| ---------------------------------------- | ------------------------------------------------------------------- |
| `WS_GATEWAY_DEMO_TOKEN`                  | Required. Must match the `token` query parameter on `/ws`.          |
| `GCP_PROJECT_ID`                         | Required for Pub/Sub + Firestore in Google Cloud.                   |
| `EVENT_NOTIFICATIONS_SUBSCRIPTION`       | Subscription **id** only, e.g. `event-notifications-ws-gateway`.    |
| `FIRESTORE_DATABASE_ID`                  | Default `default`.                                                  |
| `RECENT_ACTIONS_MAX`                     | Max **recentActions** in each snapshot; default **15**, max **50**. |
| `STATS_TIMER_INTERVAL_SEC`               | Default **10**.                                                     |
| `POPULAR_WINDOW_HOURS` / `POPULAR_LIMIT` | Firestore “popular” query.                                          |
| `DISABLE_STATS_TIMER`                    | Set to `1` to skip the Firestore refresh loop.                      |
| `PORT`, `HOST`, `LOG_LEVEL`              | As usual.                                                           |


`pytest` forces empty project and subscription and **DISABLE_STATS_TIMER=1** so it does not need real GCP.

## Health

`GET /healthz` → **200** `{"status":"ok"}`.

## Run tests

**Python 3.10+**

```powershell
cd services\ws-gateway
py -3 -m venv .venv
.\.venv\Scripts\activate
pip install -e ".[dev]"
pytest tests/ -v
```

## Cloud Run

Repo-root `.env` and `infra/scripts/32-cloud-run-ws-gateway.sh`