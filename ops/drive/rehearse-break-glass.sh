#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
: "${DOJO_SOURCE_API_URL:?Set DOJO_SOURCE_API_URL to the source API}"
: "${DOJO_RECOVERY_API_URL:?Set DOJO_RECOVERY_API_URL to the freshly bootstrapped recovery API}"
source_api_url="${DOJO_SOURCE_API_URL%/}"
recovery_api_url="${DOJO_RECOVERY_API_URL%/}"
if [[ "$source_api_url" == "$recovery_api_url" ]]; then
  printf 'Break-glass rehearsal requires distinct source and recovery APIs.\n' >&2
  exit 1
fi

# The source API creates the backup. The recovery API is used exclusively for
# restoring and cleaning up that repository after source-state loss.
DOJO_SOURCE_API_URL="$source_api_url" \
DOJO_RECOVERY_API_URL="$recovery_api_url" \
  "$repo_root/ops/drive/rehearse.sh"
