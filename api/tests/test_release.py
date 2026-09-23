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
    ("message", "expected"),
    [
        (
            "Merge pull request #14 from blogle/automation/changelog\n\n"
            "docs: synchronize published changelog [release:none]",
            "none",
        ),
        (
            "Merge pull request #15 from blogle/feat/forecasting\n\n"
            "feat: add forecasting [release:minor]",
            "minor",
        ),
    ],
)
def test_release_directive_uses_github_merge_pr_title(message: str, expected: str) -> None:
    assert release.release_directive(message) == expected


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


def test_pull_request_acknowledgement_passes_when_checked() -> None:
    release.validate_pull_request(
        "feat: add forecasting",
        "## Changelog\n\n- [x] " + release.PR_ACKNOWLEDGEMENT,
    )


@pytest.mark.parametrize("body", ["", "- [ ] " + release.PR_ACKNOWLEDGEMENT])
def test_pull_request_acknowledgement_fails_when_missing_or_unchecked(body: str) -> None:
    with pytest.raises(ValueError, match="checked changelog acknowledgement"):
        release.validate_pull_request("feat: add forecasting", body)


def test_release_none_title_exempts_pull_request_acknowledgement() -> None:
    release.validate_pull_request("chore: docs [release:none]", "")


def test_pull_request_malformed_directive_fails_closed() -> None:
    with pytest.raises(ValueError, match="Malformed release directive"):
        release.validate_pull_request("feat: docs [release:minor", "")


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


def test_sync_changelog_backfills_published_releases_without_unreleased_bucket() -> None:
    old_history = "## v0.0.4 - 2026-09-17\n\n- Old history.\n"
    existing = "# Changelog\n\n## Unreleased\n\n- Stale notes.\n\n" + old_history
    releases = [
        {"tag": "v0.0.4", "date": "2026-09-17", "body": "* legacy duplicate"},
        {"tag": "v0.0.6", "date": "2026-09-18", "body": "* release six"},
        {"tag": "v0.0.7", "date": "2026-09-20", "body": "* release seven"},
        {"tag": "v0.0.8", "date": "2026-09-20", "body": "* release eight"},
        {"tag": "v0.0.9", "date": "2026-09-21", "body": "* release nine"},
        {"tag": "v0.0.10", "date": "2026-09-22", "body": "* release ten"},
    ]

    synced = release.sync_changelog(existing, releases)

    assert "## Unreleased" not in synced
    assert "v0.0.5" not in synced
    assert synced.count("## v0.0.4 - 2026-09-17") == 1
    assert synced.index("v0.0.10") < synced.index("v0.0.9")
    assert synced.index("v0.0.9") < synced.index("v0.0.8")
    assert synced.index("v0.0.8") < synced.index("v0.0.7")
    assert synced.index("v0.0.7") < synced.index("v0.0.6")
    assert "Stale notes" not in synced
    assert synced.endswith(old_history)
    assert release.sync_changelog(synced, releases) == synced


def test_sync_changelog_replaces_generated_region_when_release_body_changes() -> None:
    existing = "# Changelog\n\n<!-- BEGIN GENERATED RELEASES -->\n\n## v0.0.6 - 2026-09-18\n\n- old\n\n<!-- END GENERATED RELEASES -->\n\n## v0.0.4 - 2026-09-17\n\n- legacy\n"
    releases = [{"tag": "v0.0.6", "date": "2026-09-18", "body": "* corrected"}]

    synced = release.sync_changelog(existing, releases)

    assert "- corrected" in synced
    assert "- old" not in synced
    assert synced.count("BEGIN GENERATED RELEASES") == 1


def test_release_workflow_syncs_changelog_on_automation_branch_and_reuses_pr() -> None:
    workflow = RELEASE_WORKFLOW.read_text(encoding="utf-8")

    assert "gh api repos/${GITHUB_REPOSITORY}/releases" in workflow
    assert "automation/changelog" in workflow
    assert 'git fetch origin "refs/heads/$branch:refs/remotes/origin/$branch"' in workflow
    assert 'git push --force-with-lease origin "$branch"' in workflow
    assert "select(.draft == false and .prerelease == false and .published_at != null)" in workflow
    assert 'body: (.body // "")' in workflow
    assert 'git push --force-with-lease origin "master"' not in workflow
    assert "gh pr list" in workflow
    assert "[release:none]" in workflow
    assert "git log -1 --pretty=%B" in workflow
    assert "git log -1 --pretty=%s" not in workflow


def test_pr_body_validator_is_pull_request_only_and_reads_event_json() -> None:
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")

    verify = workflow.split("  verify:", 1)[1].split("  publish-pr-image:", 1)[0]
    assert "Validate changelog acknowledgement" in verify
    assert "if: github.event_name == 'pull_request'" in verify
    assert 'validate-pr "$GITHUB_EVENT_PATH"' in verify
    assert verify.index("Validate changelog acknowledgement") < verify.index(
        "Install project dependencies"
    )
    assert "github.event.pull_request.body" not in workflow


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
