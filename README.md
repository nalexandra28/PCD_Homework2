# PCD Homework 2 — Real-time analytics pipeline (Fast Lazy Bee + GCP)

This repository contains an extension of the **Fast Lazy Bee** movie API into an event-driven analytics pipeline on **Google Cloud Platform**. The baseline REST application remains under `fast-lazy-bee/`; additional components provide **Pub/Sub** messaging, **Firestore**-backed analytics, a serverless consumer, a **WebSocket** gateway, and a dashboard.

## Repository layout


| Path                                                           | Description                                                       |
| -------------------------------------------------------------- | ----------------------------------------------------------------- |
| `[fast-lazy-bee/](fast-lazy-bee/)`                             | Fastify/TypeScript **REST API**                                   |
| `[services/analytics-function/](services/analytics-function/)` | **Serverless** consumer for **Pub/Sub**                           |
| `[services/ws-gateway/](services/ws-gateway/)`                 | **WebSocket** gateway                                             |
| `[dashboard/](dashboard/)`                                     | **HTML** client                                                   |
| `[infra/scripts/](infra/scripts/)`                             | **Bash** + `gcloud`: APIs, Pub/Sub, **Firestore**, **Deployment** |


## Provisioning from a clean clone

1. Select or create a GCP project; authenticate (`gcloud auth login`).
2. At the repository root, copy `[.env.example](.env.example)` to `.env` and set at least `GCP_PROJECT_ID` (and `MONGO_URL` for Atlas / deploy). Run `[infra/scripts/apply-all.sh](infra/scripts/apply-all.sh)` as in `[infra/README.md](infra/README.md)`.
3. (Optional) Seed **MongoDB** with **sample_mflix** — e.g. `[infra/scripts/15-mongorestore-sample-mflix.sh](infra/scripts/15-mongorestore-sample-mflix.sh)` .

The **dashboard** is a static folder you run locally (see `dashboard/README.md`);