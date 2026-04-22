# Infrastructure — Google Cloud SDK (`gcloud`)

Shell scripts under [`scripts/`](scripts/) provision GCP resources. `lib.sh` loads the repo-root `.env` and requires **`GCP_PROJECT_ID`**; **`GCP_REGION`** defaults to `us-central1` if unset.

## Prerequisites

1. [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) with `gcloud` on `PATH`.
2. Billing enabled on the GCP project; `gcloud auth login`.

### API enablement

`00-enable-apis.sh` enables: `pubsub.googleapis.com`, `firestore.googleapis.com`, `cloudbuild.googleapis.com`, `run.googleapis.com`, `artifactregistry.googleapis.com`.

## `.env` (repo root)

| Variable        | Required | Notes              |
| --------------- | -------- | ------------------ |
| `GCP_PROJECT_ID` | yes      |                    |
| `GCP_REGION`    | no       | default `us-central1` |
| `MONGO_URL`     | for `15-` and `30-` | Atlas SRV string; see below |

## Scripts

| Script                 | Role                                                                 |
| ---------------------- | -------------------------------------------------------------------- |
| `00-enable-apis.sh`    | Enable APIs                                                          |
| `10-pubsub-topic.sh`  | Create Pub/Sub topic `movie-events` if missing                     |
| `15-mongorestore-sample-mflix.sh` | `curl` sample_mflix archive, `mongorestore` (needs `MONGO_URL`; no `gcloud`) |
| `20-firestore-database.sh` | Create Firestore native DB `(default)` if missing                 |
| `30-cloud-run-fast-lazy-bee.sh` | Cloud Build, Artifact Registry, deploy `fast-lazy-bee`  |
| `apply-all.sh`         | Runs `00`, `10`, `20` (not `15` or `30`)                         |

## Execution

```bash
cd path/to/PCD_Homework2
cp .env.example .env
cd infra/scripts
chmod +x *.sh
./apply-all.sh
```

## MongoDB Atlas — `sample_mflix` data

The app expects a **`sample_mflix`** database (see `fast-lazy-bee` config). With [MongoDB Database Tools](https://www.mongodb.com/try/download/database-tools) on your `PATH`, you can run `./15-mongorestore-sample-mflix.sh` from `infra/scripts/` (it uses `MONGO_URL` in `.env` and stores the archive under `infra/data/`), or run the same steps by hand:

```bash
curl -fS 'https://atlas-education.s3.amazonaws.com/sample_mflix.archive' -o sample_mflix.archive
mongorestore --uri 'YOUR_MONGO_URL' --drop --archive=sample_mflix.archive
```

Replace `YOUR_MONGO_URL` with the same value as in `.env` (quoted if it contains `&` or `?`).


