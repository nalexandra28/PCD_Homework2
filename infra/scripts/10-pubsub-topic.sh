#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib.sh"

PUBSUB_TOPIC="movie-events"

if gcloud pubsub topics describe "${PUBSUB_TOPIC}" \
  --project="${GCP_PROJECT_ID}" &>/dev/null; then
  echo "Topic ${PUBSUB_TOPIC} already exists."
else
  echo "Creating topic ${PUBSUB_TOPIC} ..."
  gcloud pubsub topics create "${PUBSUB_TOPIC}" \
    --project="${GCP_PROJECT_ID}"
  echo "Created."
fi
