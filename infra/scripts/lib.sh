#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
ENV_FILE="${REPO_ROOT}/.env"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Missing ${ENV_FILE}"
  echo "Copy .env.example to .env at the repository root and set GCP_PROJECT_ID (and overrides if needed)."
  exit 1
fi

set -a
source "${ENV_FILE}"
set +a

: "${GCP_PROJECT_ID:?Set GCP_PROJECT_ID in .env at repository root}"
gcloud config set project "${GCP_PROJECT_ID}" --quiet
: "${GCP_REGION:=us-west1}"
: "${PUBSUB_TOPIC_RESOURCE_EVENTS:=movie-events}"
if [ -z "${FIRESTORE_DATABASE_ID:-}" ]; then
  export FIRESTORE_DATABASE_ID='(default)'
else
  export FIRESTORE_DATABASE_ID
fi
: "${FIRESTORE_TYPE:=firestore-native}"

export GCP_PROJECT_ID GCP_REGION PUBSUB_TOPIC_RESOURCE_EVENTS
export FIRESTORE_DATABASE_ID FIRESTORE_TYPE
