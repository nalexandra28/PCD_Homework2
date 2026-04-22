#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib.sh"

echo "Enabling APIs on project ${GCP_PROJECT_ID} ..."
gcloud services enable \
  pubsub.googleapis.com \
  firestore.googleapis.com \
  --project="${GCP_PROJECT_ID}"
echo "Done."
