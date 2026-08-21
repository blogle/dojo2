#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
profile_dir="${XDG_CACHE_HOME:-$HOME/.cache}/dojo/e2e/profiles/$(date -u +%Y%m%dT%H%M%S)-$$"
manifest="${profile_dir}/runs.txt"
mkdir -p "$profile_dir"

for run in 1 2 3; do
  printf '==> E2E profile run %s/3\n' "$run"
  DOJO_E2E_PROFILE_MANIFEST="$manifest" "$repo_root/web/scripts/run-e2e.sh"
done

node "$repo_root/web/scripts/summarize-e2e-profile.mjs" \
  "$manifest" \
  "$profile_dir/profile.json"
