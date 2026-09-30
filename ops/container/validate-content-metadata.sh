#!/usr/bin/env bash
set -euo pipefail

archive="${1:?Set the container archive path}"
manifest="$(tar -xOzf "$archive" manifest.json)"
config="$(printf '%s' "$manifest" | jq -r '.[0].Config')"
metadata="$(tar -xOzf "$archive" "$config")"

jq -e '
  ([.config.Env[]? | select(startswith("DOJO_BUILD_SHA="))] | length) == 0
  and (.config.Labels["org.opencontainers.image.revision"]? == null)
' <<<"$metadata" >/dev/null

printf 'Content image has no commit-specific build provenance.\n'
