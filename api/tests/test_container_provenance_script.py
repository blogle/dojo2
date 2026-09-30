from __future__ import annotations

import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).parents[2]
VALIDATE_IMAGE_PROVENANCE = REPO_ROOT / "ops" / "container" / "validate-image-provenance.sh"


def test_live_image_validator_passes_valid_docker_inspect_templates(tmp_path: Path) -> None:
    expected_sha = "a" * 40
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    docker = bin_dir / "docker"
    docker.write_text(
        """#!/usr/bin/env bash
set -euo pipefail

if [[ "$1 $2 $3" != "image inspect --format" ]]; then
  printf 'unexpected docker invocation: %s\\n' "$*" >&2
  exit 64
fi

case "$4" in
  '{{range .Config.Env}}{{println .}}{{end}}')
    printf 'PATH=/usr/bin\\nDOJO_BUILD_SHA=%s\\n' "$EXPECTED_SHA"
    ;;
  '{{ index .Config.Labels "org.opencontainers.image.revision" }}')
    printf '%s\\n' "$EXPECTED_SHA"
    ;;
  *)
    printf 'unexpected inspect format: <%s>\\n' "$4" >&2
    exit 64
    ;;
esac
""",
        encoding="utf-8",
    )
    docker.chmod(0o755)

    environment = {
        **os.environ,
        "PATH": f"{bin_dir}:{os.environ['PATH']}",
        "EXPECTED_SHA": expected_sha,
    }
    subprocess.run(
        [str(VALIDATE_IMAGE_PROVENANCE), "ghcr.io/blogle/dojo2:test", expected_sha],
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )
