from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

RELEASE_SCRIPT = Path(__file__).parents[2] / "scripts" / "release.py"
REPO_ROOT = RELEASE_SCRIPT.parents[1]
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"
RELEASE_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "release.yml"
SPEC = importlib.util.spec_from_file_location("dojo_release", RELEASE_SCRIPT)
assert SPEC is not None and SPEC.loader is not None
release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release)


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("fix: correct account balance", "patch"),
        ("feat: add forecasting [release:minor]", "minor"),
        ("breaking: replace budget model [release:major]", "major"),
        ("chore: remove stale fixture [release:none]", "none"),
    ],
)
def test_release_directive_defaults_and_parses_title(title: str, expected: str) -> None:
    assert release.release_directive(title) == expected


def test_release_directive_ignores_commit_body() -> None:
    title = "fix: correct balance\n\n[release:major]"

    assert release.release_directive(title) == "patch"


@pytest.mark.parametrize(
    "title",
    [
        "feat: mixed release [release:minor] [release:major]",
        "feat: invalid release [release:weekly]",
        "feat: malformed release [release:minor",
    ],
)
def test_release_directive_rejects_invalid_titles(title: str) -> None:
    with pytest.raises(ValueError):
        release.release_directive(title)


@pytest.mark.parametrize(
    ("version", "bump", "expected"),
    [
        ((0, 0, 5), "patch", (0, 0, 6)),
        ((0, 0, 5), "minor", (0, 1, 0)),
        ((0, 0, 5), "major", (1, 0, 0)),
    ],
)
def test_bump_version(
    version: tuple[int, int, int], bump: str, expected: tuple[int, int, int]
) -> None:
    assert release.bump_version(version, bump) == expected


def test_release_workflow_builds_once_and_promotes_the_immutable_image() -> None:
    workflow = RELEASE_WORKFLOW.read_text(encoding="utf-8")

    assert workflow.count("nix build .#container") == 1
    assert workflow.count("docker build --build-arg DOJO_BUILD_SHA") == 1
    assert "publish-release-image:" not in workflow
    assert "needs: [prepare-release, publish-image, tag-release]" in workflow
    assert 'docker pull "$source_image"' in workflow
    assert 'docker tag "$source_image" "$alias_image"' in workflow
    assert 'source_sha="$GITHUB_SHA"' in workflow
    assert 'git rev-parse "refs/tags/${RELEASE_TAG}^{commit}"' in workflow


def test_pr_image_workflow_does_not_overwrite_an_existing_git_tag() -> None:
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")

    assert workflow.count("nix build .#container") == 1
    assert workflow.count("docker build --build-arg DOJO_BUILD_SHA") == 1
    assert 'docker manifest inspect "$source_image"' in workflow
    assert 'docker pull "$source_image"' in workflow
    assert 'docker tag "ghcr.io/blogle/dojo2:git-${GITHUB_SHA}"' in workflow
