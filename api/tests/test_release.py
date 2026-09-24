from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

RELEASE_SCRIPT = Path(__file__).parents[2] / "scripts" / "release.py"
REPO_ROOT = RELEASE_SCRIPT.parents[1]
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"
RELEASE_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "release.yml"
MERGE_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "merge.yml"
SPEC = importlib.util.spec_from_file_location("dojo_release", RELEASE_SCRIPT)
assert SPEC is not None and SPEC.loader is not None
release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release)


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        ("", "patch"),
        ("<!-- dojo-release: patch -->", "patch"),
        ("<!-- dojo-release: minor -->", "minor"),
        ("<!-- dojo-release: major -->", "major"),
        ("<!-- dojo-release: none -->", "none"),
    ],
)
def test_release_directive_defaults_and_parses_body(body: str, expected: str) -> None:
    assert release.release_directive(body) == expected


@pytest.mark.parametrize(
    "body",
    [
        "<!-- dojo-release: weekly -->",
        "<!-- dojo-release: minor",
        "<!-- dojo-release: minor -->\n<!-- dojo-release: major -->",
    ],
)
def test_release_directive_rejects_invalid_or_conflicting_body(body: str) -> None:
    with pytest.raises(ValueError):
        release.release_directive(body)


@pytest.mark.parametrize(
    ("tags", "bump", "expected"),
    [
        (["v0.0.9", "v0.0.10", "not-a-release"], "patch", "0.0.11"),
        (["v1.2.9"], "minor", "1.3.0"),
        (["v1.2.9"], "major", "2.0.0"),
        ([], "patch", "0.0.1"),
    ],
)
def test_next_version_uses_highest_semver_tag(tags: list[str], bump: str, expected: str) -> None:
    assert release.next_version_from_tags(tags, bump) == expected


def test_release_none_has_no_version() -> None:
    with pytest.raises(ValueError, match="cannot be calculated"):
        release.next_version_from_tags(["v1.0.0"], "none")


def test_update_changelog_adds_undated_release_and_preserves_legacy_history() -> None:
    existing = """# Changelog

<!-- BEGIN GENERATED RELEASES -->

## v0.0.10 - 2026-09-22

- old generated note

<!-- END GENERATED RELEASES -->

## v0.0.4 - 2026-09-17

- legacy note
"""

    updated = release.update_changelog(
        existing, "0.0.11", "feat: ship flow", "alice", "42", "https://example.test/pull/42"
    )

    assert "## v0.0.11\n" in updated
    assert "## v0.0.10 - 2026-09-22" not in updated
    assert "## v0.0.10\n" in updated
    assert "- feat: ship flow by @alice in https://example.test/pull/42" in updated
    assert "## v0.0.4 - 2026-09-17" in updated
    assert updated.index("v0.0.11") < updated.index("v0.0.10")


def test_update_changelog_is_idempotent_and_replaces_existing_entry() -> None:
    existing = """# Changelog

<!-- BEGIN GENERATED RELEASES -->

## v1.0.0

- old

<!-- END GENERATED RELEASES -->
"""

    updated = release.update_changelog(existing, "v1.0.0", "new title", "bob", "7", "")

    assert updated.count("## v1.0.0") == 1
    assert "- new title by @bob in pull/7" in updated
    assert "- old" not in updated
    assert release.update_changelog(updated, "1.0.0", "new title", "bob", "7", "") == updated


def test_changelog_version_ignores_tagged_versions_and_legacy_dates() -> None:
    changelog = """# Changelog

<!-- BEGIN GENERATED RELEASES -->

## v1.0.2

- generated

## v1.0.1

- generated

<!-- END GENERATED RELEASES -->

## v0.9.0 - 2026-01-01

- legacy
"""

    assert release.changelog_version(changelog, ["v1.0.1"]) == "v1.0.2"
    assert release.changelog_version(changelog, ["v1.0.1", "v1.0.2"]) is None


def test_release_workflow_is_publication_only() -> None:
    workflow = RELEASE_WORKFLOW.read_text(encoding="utf-8")

    assert "changelog-version" in workflow
    assert "git log -1" not in workflow
    assert "sync-changelog" not in workflow
    assert "automation/changelog" not in workflow
    assert "gh pr create" not in workflow
    assert "--notes-file" in workflow


def test_ci_validates_pr_body_and_supports_explicit_candidate_validation() -> None:
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")

    assert "workflow_dispatch:" in workflow
    assert "validate-pr" in workflow
    assert "pull_request.body" not in workflow
    assert "inputs.ref" in workflow
    assert "inputs.sha" in workflow
    assert "statuses: write" in workflow


def test_merge_workflow_is_exact_comment_and_revalidates_before_squash() -> None:
    workflow = MERGE_WORKFLOW.read_text(encoding="utf-8")

    assert "issue_comment:" in workflow
    assert "github.event.comment.body == '/merge'" in workflow
    assert "collaborators" in workflow
    assert "merge-base --is-ancestor" in workflow
    assert "workflow run" in workflow
    assert "git push" in workflow
    assert "merge_method=squash" in workflow
    assert "master-merge" in workflow
