#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
: "${DOJO_BREAK_GLASS_API_URL:?Set DOJO_BREAK_GLASS_API_URL to the freshly bootstrapped recovery API}"

# The ordinary rehearsal creates its source database locally, while this URL
# points at the separately provisioned recovery API/database.
DOJO_API_URL="$DOJO_BREAK_GLASS_API_URL" \
  "$repo_root/ops/drive/rehearse.sh"
