#!/usr/bin/env bash
set -euo pipefail

commit="${1:?Usage: publish-image.sh <full-lowercase-commit-sha>}"
if [[ ! "$commit" =~ ^[0-9a-f]{40}$ ]]; then
  printf 'Invalid commit SHA: %s\n' "$commit" >&2
  exit 2
fi

tree="$(git rev-parse "${commit}^{tree}")"
if [[ ! "$tree" =~ ^[0-9a-f]{40}$ ]]; then
  printf 'Invalid Git tree SHA: %s\n' "$tree" >&2
  exit 2
fi

registry="ghcr.io/blogle/dojo2"
git_image="${registry}:git-${commit}"
content_image="${registry}:content-${tree}"

validate_git_image() {
  local image="$1"
  local image_env image_revision
  image_env="$(docker image inspect --format '{{range .Config.Env}}{{println .}}{{end}}' "$image")"
  image_revision="$(docker image inspect --format '{{ index .Config.Labels "org.opencontainers.image.revision" }}' "$image")"
  if ! printf '%s\n' "$image_env" | grep -Fqx -- "DOJO_BUILD_SHA=$commit" \
    || [[ "$image_revision" != "$commit" ]]; then
    printf 'Image %s does not contain exact commit provenance for %s.\n' "$image" "$commit" >&2
    exit 1
  fi
}

if docker manifest inspect "$git_image" >/dev/null 2>&1; then
  printf 'mode=git-image-hit image=%s\n' "$git_image"
  docker pull "$git_image"
  validate_git_image "$git_image"
  exit 0
fi

if docker manifest inspect "$content_image" >/dev/null 2>&1; then
  printf 'mode=content-image-hit image=%s\n' "$content_image"
  docker pull "$content_image"
else
  printf 'mode=content-build image=%s\n' "$content_image"
  nix develop --command just setup-web
  nix develop --command just build-web
  nix build .#container
  docker load < "$(readlink -f result)"
  docker build --file ops/container/Dockerfile.content --tag "$content_image" .
  # A concurrent publisher may have completed the same tree while this runner
  # built it. Reuse that immutable-by-tree artifact if it is already visible.
  if docker manifest inspect "$content_image" >/dev/null 2>&1; then
    docker pull "$content_image"
  else
    docker push "$content_image"
  fi
fi

docker build --file Dockerfile \
  --build-arg "CONTENT_IMAGE=$content_image" \
  --build-arg "DOJO_BUILD_SHA=$commit" \
  --tag "$git_image" .
validate_git_image "$git_image"
docker push "$git_image"
