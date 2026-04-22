# Infrastructure — Google Cloud SDK (`gcloud`)

This document describes how to provision **Pub/Sub** and **Cloud Firestore** for the **PCD** homework project using the shell scripts under [`scripts/`](scripts/).

## Region

The default region is `us-west1`. The same value should appear in the repository-root `.env` and in any runtime configuration.

## Prerequisites

1. [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed, with `gcloud` on `PATH`.
2. A GCP project with billing enabled.
3. User authentication: `gcloud auth login`.

### API enablement

The first script enables `pubsub.googleapis.com` and `firestore.googleapis.com`.

## Resources created

| Resource type   | Default identifier |
| --------------- | ------------------ |
| Pub/Sub topic   | `movie-events` (override: `PUBSUB_TOPIC_RESOURCE_EVENTS`) |
| Firestore (native) | Id `(default)`, `firestore-native`, `--location` = `GCP_REGION` |

## Execution (clean clone)

### Bash (Linux, WSL)

```bash
cd path/to/PCD_Homework2
cp .env.example .env
cd infra/scripts
chmod +x *.sh
./apply-all.sh
```

Edit the repository-root `.env` before execution; scripts load `../../.env` relative to `infra/scripts/`.

### Verification

- `gcloud config get-value project`
- `gcloud services list --enabled | grep -E 'pubsub|firestore'`
- `gcloud pubsub topics describe resource-events --project=YOUR_PROJECT_ID`
- `gcloud firestore databases list --project=YOUR_PROJECT_ID`

The repository-root `.env` must remain untracked (see root `.gitignore`).
