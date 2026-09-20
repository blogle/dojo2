#!/usr/bin/env bash
set -euo pipefail

archive="${1:?Set the container archive path}"
expected_sha="${2:?Set the expected full Git SHA}"
manifest="$(tar -xOzf "$archive" manifest.json)"
config="$(printf '%s' "$manifest" | jq -r '.[0].Config')"
metadata="$(tar -xOzf "$archive" "$config")"

jq -e --arg expected_sha "$expected_sha" \
  '.config.Env | index("DOJO_BUILD_SHA=" + $expected_sha) != null' \
  <<<"$metadata" >/dev/null
jq -e --arg expected_sha "$expected_sha" \
  '.config.Labels["org.opencontainers.image.revision"] == $expected_sha' \
  <<<"$metadata" >/dev/null

printf 'Container build metadata contains Git SHA %s.\n' "$expected_sha"
