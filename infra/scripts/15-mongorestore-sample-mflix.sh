#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
ARCHIVE="${REPO_ROOT}/infra/data/sample_mflix.archive"
URL="https://atlas-education.s3.amazonaws.com/sample_mflix.archive"

[[ -f "${REPO_ROOT}/.env" ]] || { echo "Missing ${REPO_ROOT}/.env"; exit 1; }
set -a
source "${REPO_ROOT}/.env"
set +a
: "${MONGO_URL:?}"

mkdir -p "$(dirname "${ARCHIVE}")"
[[ -f "${ARCHIVE}" ]] || curl -fS "${URL}" -o "${ARCHIVE}"
mongorestore --uri="${MONGO_URL}" --drop --archive="${ARCHIVE}"
