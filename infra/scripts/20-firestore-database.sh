#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib.sh"

if gcloud firestore databases describe \
  --database="${FIRESTORE_DATABASE_ID}" \
  --project="${GCP_PROJECT_ID}" &>/dev/null; then
  echo "Database ${FIRESTORE_DATABASE_ID} already exists."
else
  echo "Creating database ${FIRESTORE_DATABASE_ID} ..."
  gcloud firestore databases create \
    --database="${FIRESTORE_DATABASE_ID}" \
    --location="${GCP_REGION}" \
    --type="${FIRESTORE_TYPE}" \
    --project="${GCP_PROJECT_ID}"
  echo "Created."
fi
