#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
source "${SCRIPT_DIR}/lib.sh"

: "${WS_GATEWAY_DEMO_TOKEN:?Set WS_GATEWAY_DEMO_TOKEN in repo-root .env (demo shared secret for WebSocket upgrade)}"

PROJECT_NUMBER="$(gcloud projects describe "${GCP_PROJECT_ID}" --format='value(projectNumber)')"
COMPUTE_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
gcloud projects add-iam-policy-binding "${GCP_PROJECT_ID}" \
  --member="serviceAccount:${COMPUTE_SA}" \
  --role="roles/datastore.user" \
  --quiet
gcloud projects add-iam-policy-binding "${GCP_PROJECT_ID}" \
  --member="serviceAccount:${COMPUTE_SA}" \
  --role="roles/pubsub.subscriber" \
  --quiet

AR_REPOSITORY="myrepo"
AR_IMAGE="ws-gateway"
AR_TAG="v1"
CLOUD_RUN_SERVICE="ws-gateway"
APP_PORT=8080

PROJECT_NUMBER="$(gcloud projects describe "${GCP_PROJECT_ID}" --format='value(projectNumber)')"
CB_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"
gcloud projects add-iam-policy-binding "${GCP_PROJECT_ID}" \
  --member="serviceAccount:${CB_SA}" \
  --role="roles/cloudbuild.builds.builder" \
  --quiet

COMPUTE_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
gcloud projects add-iam-policy-binding "${GCP_PROJECT_ID}" \
  --member="serviceAccount:${COMPUTE_SA}" \
  --role="roles/logging.logWriter" \
  --quiet

gcloud projects add-iam-policy-binding "${GCP_PROJECT_ID}" \
  --member="serviceAccount:${COMPUTE_SA}" \
  --role="roles/cloudbuild.builds.builder" \
  --quiet

APP_DIR="${REPO_ROOT}/services/ws-gateway"
IMAGE="${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${AR_REPOSITORY}/${AR_IMAGE}:${AR_TAG}"

if ! gcloud artifacts repositories describe "${AR_REPOSITORY}" \
  --location="${GCP_REGION}" --project="${GCP_PROJECT_ID}" &>/dev/null; then
  echo "Creating Artifact Registry repo ${AR_REPOSITORY} ..."
  gcloud artifacts repositories create "${AR_REPOSITORY}" \
    --repository-format=docker \
    --location="${GCP_REGION}" \
    --project="${GCP_PROJECT_ID}" \
    --description="PCD"
fi

echo "Build + push ${IMAGE} ..."
gcloud builds submit "${APP_DIR}" --tag="${IMAGE}" --project="${GCP_PROJECT_ID}"

echo "Deploy ${CLOUD_RUN_SERVICE} ..."
NOTIF_SUB="${EVENT_NOTIFICATIONS_SUBSCRIPTION:-event-notifications-ws-gateway}"
FS_ID="${FIRESTORE_DATABASE_ID:-$'(default)'}"

gcloud run deploy "${CLOUD_RUN_SERVICE}" \
  --image="${IMAGE}" \
  --platform=managed \
  --region="${GCP_REGION}" \
  --allow-unauthenticated \
  --port="${APP_PORT}" \
  --min-instances=0 \
  --max-instances=2 \
  --set-env-vars="WS_GATEWAY_DEMO_TOKEN=${WS_GATEWAY_DEMO_TOKEN},LOG_LEVEL=INFO,GCP_PROJECT_ID=${GCP_PROJECT_ID},EVENT_NOTIFICATIONS_SUBSCRIPTION=${NOTIF_SUB},FIRESTORE_DATABASE_ID=${FS_ID},STATS_TIMER_INTERVAL_SEC=1" \
  --project="${GCP_PROJECT_ID}"

echo "Done."
