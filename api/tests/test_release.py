from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

RELEASE_SCRIPT = Path(__file__).parents[2] / "scripts" / "release.py"
REPO_ROOT = RELEASE_SCRIPT.parents[1]
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"
RELEASE_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "release.yml"
MERGE_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "merge.yml"
PR_TEMPLATE = REPO_ROOT / ".github" / "pull_request_template.md"
SPEC = importlib.util.spec_from_file_location("dojo_release", RELEASE_SCRIPT)
assert SPEC is not None and SPEC.loader is not None
release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release)


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        ("", "patch"),
        ("[release:patch]", "patch"),
        ("[release:minor]", "minor"),
        ("[release:major]", "major"),
        ("[release:none]", "none"),
    ],
)
def test_release_directive_defaults_and_parses_body(body: str, expected: str) -> None:
    assert release.release_directive(body) == expected


@pytest.mark.parametrize(
    "body",
    [
        "[release:weekly]",
        "[release:minor",
        "[release:minor]\n[release:major]",
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


def test_next_version_advances_past_untagged_checked_in_release() -> None:
    changelog = """# Changelog

<!-- BEGIN GENERATED RELEASES -->

## v0.0.11

- pending release

<!-- END GENERATED RELEASES -->
"""

    assert release.next_version_from_state(["v0.0.10"], changelog) == "0.0.12"


def test_introduced_release_version_returns_none_for_no_delta() -> None:
    changelog = (
        "# Changelog\n\n<!-- BEGIN GENERATED RELEASES -->\n\n<!-- END GENERATED RELEASES -->\n"
    )

    assert release.introduced_release_version(changelog, changelog) is None


def test_introduced_release_version_returns_one_added_version() -> None:
    parent = "# Changelog\n\n<!-- BEGIN GENERATED RELEASES -->\n\n<!-- END GENERATED RELEASES -->\n"
    current = parent.replace(
        "<!-- END GENERATED RELEASES -->",
        "## v0.0.11\n\n- release\n\n<!-- END GENERATED RELEASES -->",
    )

    assert release.introduced_release_version(parent, current) == "v0.0.11"


def test_introduced_release_version_rejects_multiple_added_versions() -> None:
    parent = "# Changelog\n\n<!-- BEGIN GENERATED RELEASES -->\n\n<!-- END GENERATED RELEASES -->\n"
    current = parent.replace(
        "<!-- END GENERATED RELEASES -->",
        "## v0.0.11\n\n- one\n\n## v0.0.12\n\n- two\n\n<!-- END GENERATED RELEASES -->",
    )

    with pytest.raises(ValueError, match="multiple generated release versions"):
        release.introduced_release_version(parent, current)


def test_latest_status_states_uses_latest_status_per_context() -> None:
    statuses = [
        {
            "context": "ci/test",
            "state": "success",
            "updated_at": "2026-09-24T10:00:00Z",
        },
        {
            "context": "ci/test",
            "state": "failure",
            "updated_at": "2026-09-24T09:00:00Z",
        },
        {"context": "lint", "state": "success", "created_at": "2026-09-24T08:00:00Z"},
    ]

    assert release.latest_status_states(statuses) == {
        "ci/test": "success",
        "lint": "success",
    }


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

    assert "changelog-delta" in workflow
    assert "group: dojo-master-release" not in workflow
    assert (
        "group: dojo-release-${{ github.event_name == 'workflow_dispatch' && inputs.commit || github.sha }}"
        in workflow
    )
    assert (
        "ref: ${{ github.event_name == 'workflow_dispatch' && inputs.commit || github.sha }}"
        in workflow
    )
    assert "${{ needs.prepare-release.outputs.commit }}" in workflow
    assert "workflow_dispatch:" in workflow
    assert "description: Exact master commit to publish" in workflow
    assert "required: true" in workflow
    assert "TARGET_COMMIT" in workflow
    assert 'git merge-base --is-ancestor "$TARGET_COMMIT" origin/master' in workflow
    assert "ref: master" not in workflow
    assert "publish-staging:" in workflow
    assert "ghcr.io/blogle/dojo2:staging" in workflow
    assert "git ls-remote origin refs/heads/master" in workflow
    assert "leaving staging unchanged" in workflow
    assert 'git show "${parent}:CHANGELOG.md"' in workflow
    assert "git log -1" not in workflow
    assert "changelog-version" not in workflow
    assert "sync-changelog" not in workflow
    assert "automation/changelog" not in workflow
    assert "gh pr create" not in workflow
    assert "--notes-file" in workflow
    assert "gh release edit" in workflow


def test_pr_template_defaults_to_required_body_directive() -> None:
    template = PR_TEMPLATE.read_text(encoding="utf-8")

    assert "[release:patch]" in template
    assert "dojo-release" not in template


def test_ci_validates_pr_body_and_supports_explicit_candidate_validation() -> None:
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")

    assert "workflow_dispatch:" in workflow
    assert "validate-pr" in workflow
    assert "pull_request.body" not in workflow
    assert "description: Candidate branch to validate" in workflow
    assert "inputs.sha" in workflow
    assert "inputs.context" in workflow
    assert "ref: ${{ github.event_name == 'workflow_dispatch' && inputs.sha" in workflow
    assert "statuses: write" in workflow


def test_merge_workflow_is_exact_comment_and_revalidates_before_squash() -> None:
    workflow = MERGE_WORKFLOW.read_text(encoding="utf-8")

    assert "issue_comment:" in workflow
    assert "github.event.comment.body == '/merge'" in workflow
    assert "collaborators" in workflow
    assert "merge-base --is-ancestor" in workflow
    assert "workflow run" in workflow
    assert "gh run list" not in workflow
    assert "validation_context" in workflow
    assert ".statuses" in workflow
    assert 'git rev-parse origin/master)" == "$master_sha"' in workflow
    assert "git push" in workflow
    assert "merge_method=squash" in workflow
    assert "the PR title changed after validation" in workflow
    assert "the PR release directive changed after validation" in workflow
    assert "group_by(.context)" in workflow
    assert "merge_sha=\"$(jq -r '.sha // empty'" in workflow
    assert 'gh workflow run release.yml --ref master -f commit="$merge_sha"' in workflow
    assert "master-merge" in workflow
