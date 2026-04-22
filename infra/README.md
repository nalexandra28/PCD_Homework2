# Infrastructure — Google Cloud SDK (`gcloud`)

This document describes how to provision **Pub/Sub** for the **PCD** homework project using the shell scripts under `[scripts/](scripts/)`. 

## Region

The default region is `us-west1`. The same value should appear in the repository-root `.env` and in any runtime configuration.

## Prerequisites

1. [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed, with `gcloud` on `PATH`.
2. A GCP project with billing enabled.
3. User authentication: `gcloud auth login`.

### API enablement

The first script in the sequence enables `pubsub.googleapis.com`.

## Resources created


| Resource type | Default identifier                                           |
| ------------- | ------------------------------------------------------------ |
| Pub/Sub topic | `resource-events` (override: `PUBSUB_TOPIC_RESOURCE_EVENTS`) |


## Execution (clean clone)

### Bash (Linux, macOS, Git Bash, WSL, Cloud Shell)

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
- `gcloud services list --enabled`
- `gcloud pubsub topics describe resource-events`

The repository-root `.env` must remain untracked (see root `.gitignore`).

