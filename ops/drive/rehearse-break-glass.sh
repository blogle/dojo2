#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
: "${DOJO_SOURCE_API_URL:?Set DOJO_SOURCE_API_URL to the source API}"
: "${DOJO_RECOVERY_API_URL:?Set DOJO_RECOVERY_API_URL to the freshly bootstrapped recovery API}"

# The source API creates the backup. The recovery API is used exclusively for
# restoring and cleaning up that repository after source-state loss.
DOJO_SOURCE_API_URL="$DOJO_SOURCE_API_URL" \
DOJO_RECOVERY_API_URL="$DOJO_RECOVERY_API_URL" \
  "$repo_root/ops/drive/rehearse.sh"
