#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib.sh"

"${SCRIPT_DIR}/00-enable-apis.sh"
"${SCRIPT_DIR}/10-pubsub-topic.sh"
"${SCRIPT_DIR}/20-firestore-database.sh"

echo ""
echo "All steps finished. Topic: movie-events | Firestore: (default) (project ${GCP_PROJECT_ID}, region ${GCP_REGION})"
