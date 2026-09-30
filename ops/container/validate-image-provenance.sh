#!/usr/bin/env bash
set -euo pipefail

image="${1:?Set the container image reference}"
expected_sha="${2:?Set the expected full Git SHA}"
if [[ ! "$expected_sha" =~ ^[0-9a-f]{40}$ ]]; then
  printf 'Invalid expected Git SHA: %s\n' "$expected_sha" >&2
  exit 2
fi

image_env="$(docker image inspect --format '{{range .Config.Env}}{{println .}}{{end}}' "$image")"
image_revision="$(docker image inspect --format '{{ index .Config.Labels "org.opencontainers.image.revision" }}' "$image")"
if ! printf '%s\n' "$image_env" | grep -Fqx -- "DOJO_BUILD_SHA=$expected_sha" \
  || [[ "$image_revision" != "$expected_sha" ]]; then
  printf 'Image %s does not contain exact commit provenance for %s.\n' "$image" "$expected_sha" >&2
  exit 1
fi
