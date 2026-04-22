#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib.sh"

if gcloud pubsub topics describe "${PUBSUB_TOPIC_RESOURCE_EVENTS}" \
  --project="${GCP_PROJECT_ID}" &>/dev/null; then
  echo "Topic ${PUBSUB_TOPIC_RESOURCE_EVENTS} already exists."
else
  echo "Creating topic ${PUBSUB_TOPIC_RESOURCE_EVENTS} ..."
  gcloud pubsub topics create "${PUBSUB_TOPIC_RESOURCE_EVENTS}" \
    --project="${GCP_PROJECT_ID}"
  echo "Created."
fi
