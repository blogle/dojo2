from __future__ import annotations

import importlib.util
import io
import json
import os
import subprocess
import tarfile
import tempfile
from pathlib import Path

import pytest

RELEASE_SCRIPT = Path(__file__).parents[2] / "scripts" / "release.py"
REPO_ROOT = RELEASE_SCRIPT.parents[1]
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"
RELEASE_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "release.yml"
MERGE_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "merge.yml"
PR_TEMPLATE = REPO_ROOT / ".github" / "pull_request_template.md"
PUBLISH_IMAGE = REPO_ROOT / "ops" / "container" / "publish-image.sh"
VALIDATE_BUILD_METADATA = REPO_ROOT / "ops" / "container" / "validate-build-metadata.sh"
VALIDATE_CONTENT_METADATA = REPO_ROOT / "ops" / "container" / "validate-content-metadata.sh"
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


def test_release_directive_ignores_inline_explanatory_syntax() -> None:
    body = """[release:none]

The supported values are `[release:patch|minor|major|none]`.
"""

    assert release.release_directive(body) == "none"


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


def test_introduced_release_version_is_stable_after_publication() -> None:
    parent = "# Changelog\n\n<!-- BEGIN GENERATED RELEASES -->\n\n<!-- END GENERATED RELEASES -->\n"
    current = parent.replace(
        "<!-- END GENERATED RELEASES -->",
        "## v0.0.11\n\n- one\n\n<!-- END GENERATED RELEASES -->",
    )

    assert (
        release.introduced_release_version(
            parent,
            current,
            ["v0.0.11"],
            associated_release_tags=["v0.0.11"],
        )
        == "v0.0.11"
    )


def test_published_backfill_only_delta_is_not_a_new_release() -> None:
    parent = "# Changelog\n\n<!-- BEGIN GENERATED RELEASES -->\n\n<!-- END GENERATED RELEASES -->\n"
    current = parent.replace(
        "<!-- END GENERATED RELEASES -->",
        "## v0.0.11\n\n- old\n\n## v0.0.12\n\n- old\n\n<!-- END GENERATED RELEASES -->",
    )

    assert release.introduced_release_version(parent, current, ["v0.0.11", "v0.0.12"]) is None


def test_published_backfills_and_one_new_release_select_only_new_version() -> None:
    parent = "# Changelog\n\n<!-- BEGIN GENERATED RELEASES -->\n\n<!-- END GENERATED RELEASES -->\n"
    current = parent.replace(
        "<!-- END GENERATED RELEASES -->",
        "## v0.0.11\n\n- old\n\n## v0.0.12\n\n- old\n\n## v0.0.13\n\n- new\n\n<!-- END GENERATED RELEASES -->",
    )

    assert release.introduced_release_version(parent, current, ["v0.0.11", "v0.0.12"]) == "v0.0.13"


def test_introduced_release_with_conflicting_published_tag_fails_in_resolution() -> None:
    parent = "# Changelog\n\n<!-- BEGIN GENERATED RELEASES -->\n\n<!-- END GENERATED RELEASES -->\n"
    current = parent.replace(
        "<!-- END GENERATED RELEASES -->",
        "## v0.0.13\n\n- new\n\n<!-- END GENERATED RELEASES -->",
    )

    with pytest.raises(ValueError, match="point to another source commit"):
        release.introduced_release_version(
            parent,
            current,
            published_tags=["v0.0.13"],
            conflicting_published_tags=["v0.0.13"],
        )


def test_exact_source_tag_takes_precedence_over_published_backfill_filter() -> None:
    parent = "# Changelog\n\n<!-- BEGIN GENERATED RELEASES -->\n\n<!-- END GENERATED RELEASES -->\n"
    current = parent.replace(
        "<!-- END GENERATED RELEASES -->",
        "## v0.0.11\n\n- backfill\n\n## v0.0.12\n\n- introduced\n\n<!-- END GENERATED RELEASES -->",
    )

    assert (
        release.introduced_release_version(
            parent,
            current,
            ["v0.0.11", "v0.0.12"],
            associated_release_tags=["v0.0.12"],
        )
        == "v0.0.12"
    )


def test_multiple_release_tags_for_source_commit_fail_deterministically() -> None:
    parent = "# Changelog\n\n<!-- BEGIN GENERATED RELEASES -->\n\n<!-- END GENERATED RELEASES -->\n"
    current = parent.replace(
        "<!-- END GENERATED RELEASES -->",
        "## v0.0.11\n\n- one\n\n## v0.0.12\n\n- two\n\n<!-- END GENERATED RELEASES -->",
    )

    with pytest.raises(ValueError, match="multiple release tags"):
        release.introduced_release_version(
            parent,
            current,
            associated_release_tags=["v0.0.11", "v0.0.12"],
        )


def test_no_release_commit_stays_no_release_when_tags_exist() -> None:
    changelog = (
        "# Changelog\n\n<!-- BEGIN GENERATED RELEASES -->\n\n<!-- END GENERATED RELEASES -->\n"
    )

    assert release.introduced_release_version(changelog, changelog, ["v0.0.11"]) is None


def test_existing_tag_for_intended_version_and_commit_is_reused() -> None:
    release.validate_tag_target("commit-x", "commit-x", "1.2.3")


def test_existing_tag_for_intended_version_on_another_commit_fails() -> None:
    with pytest.raises(ValueError, match="expected commit-x"):
        release.validate_tag_target("commit-y", "commit-x", "1.2.3")


@pytest.mark.parametrize(
    ("master_state", "source_digest", "staging_digest", "expected_state"),
    [
        ("current", "sha256:source", "sha256:source", "skip"),
        ("current", "sha256:source", "sha256:stale", "update"),
        ("advanced", "sha256:source", "sha256:stale", "skip"),
        ("current", "", "", "update"),
    ],
)
def test_staging_update_is_only_needed_for_current_master_with_missing_or_stale_image(
    master_state: str,
    source_digest: str,
    staging_digest: str,
    expected_state: str,
) -> None:
    assert release.staging_update_needed(
        master_state == "current", source_digest, staging_digest
    ) is (expected_state == "update")


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
    assert "validate-tag-target" in workflow
    assert "complete=true" in workflow
    assert "notes, and promoted image digest are complete" in workflow
    assert "packages: read" in workflow
    assert "complete != 'true'" in workflow
    assert "staging-needed" in workflow
    publish_staging = workflow.split("publish-staging:", 1)[1].split("  tag-release:", 1)[0]
    assert "if: needs.prepare-release.outputs.complete" not in publish_staging
    assert "steps.staging.outputs.skip != 'true'" in publish_staging
    assert "python3 scripts/release.py changelog-delta" in workflow
    assert "--published-tag" in workflow
    assert "--associated-tag" in workflow
    assert "--conflicting-tag" in workflow
    assert "changelog-introduces" in workflow
    assert 'git rev-parse "${tag}^{commit}"' in workflow
    assert "release_query_succeeded=true" in workflow
    assert "package_query_succeeded=true" in workflow
    assert 'release_query_succeeded" == true' in workflow
    assert 'package_query_succeeded" == true' in workflow
    assert "@json" not in workflow
    assert "fromjson" not in workflow
    assert ".metadata.container.tags // []" in workflow
    assert "package_versions" not in workflow
    assert "/users/blogle/packages/container/dojo2/versions" in workflow
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
    publish_staging = workflow.split("publish-staging:", 1)[1].split("  tag-release:", 1)[0]
    assert 'ops/container/publish-image.sh "$MASTER_COMMIT"' in publish_staging
    assert 'docker pull "$source_image"' in publish_staging
    assert "ghcr.io/blogle/dojo2:v${VERSION}" in workflow
    assert 'docker pull "$source_image"' in workflow
    assert 'ops/container/validate-image-provenance.sh "$source_image" "$MASTER_COMMIT"' in workflow
    assert 'docker tag "$source_image" "$release_image"' in workflow
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


def run_image_publisher(mode: str, commit: str, *, revision: str | None = None) -> str:
    with tempfile.TemporaryDirectory() as directory:
        bin_dir = Path(directory) / "bin"
        bin_dir.mkdir()
        log = Path(directory) / "commands.log"
        git = bin_dir / "git"
        git.write_text(
            '#!/usr/bin/env bash\nprintf \'git %s\\n\' "$*" >> "$COMMAND_LOG"\n'
            "printf '%s\\n' 'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'\n",
            encoding="utf-8",
        )
        docker = bin_dir / "docker"
        docker.write_text(
            '#!/usr/bin/env bash\nprintf \'docker %s\\n\' "$*" >> "$COMMAND_LOG"\n'
            "if [[ \"$1 $2\" == 'manifest inspect' ]]; then "
            'case "$3" in *git-*) [[ "$IMAGE_MODE" == git-hit ]] && exit 0;; '
            '*content-*) [[ "$IMAGE_MODE" == git-hit || "$IMAGE_MODE" == content-hit ]] && exit 0;; esac; exit 1; fi\n'
            'if [[ "$1 $2" == "image inspect" ]]; then '
            'if [[ "$4" == *Labels* ]]; then printf "%s\\n" "$REVISION"; '
            'else printf "%s\\n" "DOJO_BUILD_SHA=$BUILD_SHA"; fi; fi\n'
            'if [[ "$1" == load ]]; then while IFS= read -r _; do :; done; fi\n',
            encoding="utf-8",
        )
        nix = bin_dir / "nix"
        nix.write_text(
            '#!/usr/bin/env bash\nprintf \'nix %s\\n\' "$*" >> "$COMMAND_LOG"\n',
            encoding="utf-8",
        )
        readlink = bin_dir / "readlink"
        readlink.write_text("#!/usr/bin/env bash\nprintf image.tar\n", encoding="utf-8")
        for executable in (git, docker, nix, readlink):
            executable.chmod(0o755)
        result = Path(directory) / "result"
        result.write_text("fake archive", encoding="utf-8")
        (Path(directory) / "image.tar").write_text("fake image", encoding="utf-8")
        environment = {
            **os.environ,
            "PATH": f"{bin_dir}:{os.environ['PATH']}",
            "COMMAND_LOG": str(log),
            "IMAGE_MODE": mode,
            "REVISION": revision or commit,
            "BUILD_SHA": commit,
        }
        completed = subprocess.run(
            [str(PUBLISH_IMAGE), commit],
            cwd=directory,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        )
        return completed.stdout + log.read_text(encoding="utf-8")


def test_publisher_reuses_same_tree_content_without_expensive_builds() -> None:
    commands = run_image_publisher("content-hit", "a" * 40)

    assert "mode=content-image-hit" in commands
    assert "docker pull ghcr.io/blogle/dojo2:content-" in commands
    assert "docker build --file Dockerfile" in commands
    assert "just build-web" not in commands
    assert "nix build .#container" not in commands


def test_publisher_content_miss_builds_content_before_provenance_wrapper() -> None:
    commands = run_image_publisher("miss", "a" * 40)

    assert "just build-web" in commands
    assert "nix build .#container" in commands
    assert "docker build --file ops/container/Dockerfile.content" in commands
    assert commands.index("docker push ghcr.io/blogle/dojo2:content-") < commands.index(
        "docker build --file Dockerfile"
    )


def test_publisher_exact_git_hit_does_not_build() -> None:
    commands = run_image_publisher("git-hit", "a" * 40)

    assert "docker pull ghcr.io/blogle/dojo2:git-" in commands
    assert "just build-web" not in commands
    assert "docker build" not in commands
    assert "docker image inspect" in commands


def test_publisher_rejects_existing_git_image_with_wrong_provenance() -> None:
    with pytest.raises(subprocess.CalledProcessError):
        run_image_publisher("git-hit", "a" * 40, revision="b" * 40)


def test_container_content_is_neutral_and_commit_wrapper_sets_exact_provenance() -> None:
    nix_expression = (REPO_ROOT / "flake.nix").read_text(encoding="utf-8")
    content_dockerfile = (REPO_ROOT / "ops/container/Dockerfile.content").read_text(
        encoding="utf-8"
    )
    wrapper_dockerfile = (REPO_ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "DOJO_BUILD_SHA" not in nix_expression
    assert "org.opencontainers.image.revision" not in nix_expression
    assert "FROM dojo:latest" in content_dockerfile
    assert "COPY web/dist/ /share/dojo/" in content_dockerfile
    assert "FROM ${CONTENT_IMAGE}" in wrapper_dockerfile
    assert "ENV DOJO_BUILD_SHA=${DOJO_BUILD_SHA}" in wrapper_dockerfile
    assert "LABEL org.opencontainers.image.revision=${DOJO_BUILD_SHA}" in wrapper_dockerfile
    assert "COPY" not in wrapper_dockerfile


def make_docker_archive(
    directory: str,
    *,
    env: list[str],
    revision: str | None,
    compressed: bool,
) -> Path:
    archive = Path(directory) / ("image.tar.gz" if compressed else "image.tar")
    config_path = "config.json"
    labels = {} if revision is None else {"org.opencontainers.image.revision": revision}
    config = json.dumps({"config": {"Env": env, "Labels": labels}}).encode()
    manifest = json.dumps([{"Config": config_path, "RepoTags": [], "Layers": []}]).encode()
    with tarfile.open(archive, "w:gz" if compressed else "w") as container:
        for name, content in (("manifest.json", manifest), (config_path, config)):
            info = tarfile.TarInfo(name)
            info.size = len(content)
            container.addfile(info, io.BytesIO(content))
    return archive


@pytest.mark.parametrize("archive_format", ["plain-tar", "gzip"])
def test_final_master_image_validator_requires_exact_build_sha_and_oci_revision(
    archive_format: str,
) -> None:
    compressed = archive_format == "gzip"
    master_commit = "a" * 40
    with tempfile.TemporaryDirectory() as directory:
        valid_image = make_docker_archive(
            directory,
            env=[f"DOJO_BUILD_SHA={master_commit}"],
            revision=master_commit,
            compressed=compressed,
        )
        subprocess.run(
            [str(VALIDATE_BUILD_METADATA), str(valid_image), master_commit],
            check=True,
            capture_output=True,
            text=True,
        )

        invalid_image = make_docker_archive(
            directory,
            env=[f"DOJO_BUILD_SHA={'b' * 40}"],
            revision="b" * 40,
            compressed=compressed,
        )
        result = subprocess.run(
            [str(VALIDATE_BUILD_METADATA), str(invalid_image), master_commit],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0


@pytest.mark.parametrize("archive_format", ["plain-tar", "gzip"])
def test_content_image_validator_rejects_commit_specific_provenance(
    archive_format: str,
) -> None:
    compressed = archive_format == "gzip"
    with tempfile.TemporaryDirectory() as directory:
        neutral_content = make_docker_archive(
            directory, env=[], revision=None, compressed=compressed
        )
        subprocess.run(
            [str(VALIDATE_CONTENT_METADATA), str(neutral_content)],
            check=True,
            capture_output=True,
            text=True,
        )

        misleading_content = make_docker_archive(
            directory,
            env=[f"DOJO_BUILD_SHA={'a' * 40}"],
            revision="a" * 40,
            compressed=compressed,
        )
        result = subprocess.run(
            [str(VALIDATE_CONTENT_METADATA), str(misleading_content)],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0


def test_pr_publisher_uses_pr_head_and_staging_rechecks_master_before_move() -> None:
    ci = CI_WORKFLOW.read_text(encoding="utf-8")
    release_workflow = RELEASE_WORKFLOW.read_text(encoding="utf-8")
    publish_pr = ci.split("publish-pr-image:", 1)[1]
    staging = release_workflow.split("publish-staging:", 1)[1].split("  tag-release:", 1)[0]
    move_staging = staging.split("- name: Move staging", 1)[1]

    assert 'ops/container/publish-image.sh "$PR_HEAD_SHA"' in publish_pr
    assert 'docker tag "ghcr.io/blogle/dojo2:git-${PR_HEAD_SHA}"' in publish_pr
    assert move_staging.index("git ls-remote origin refs/heads/master") > move_staging.index(
        'docker pull "$source_image"'
    )
    assert 'if [[ "$remote_master" != "$MASTER_COMMIT" ]]' in move_staging

    promote_release = release_workflow.split("publish-release-image:", 1)[1]
    assert (
        promote_release.index('docker pull "$source_image"')
        < promote_release.index(
            'ops/container/validate-image-provenance.sh "$source_image" "$MASTER_COMMIT"'
        )
        < promote_release.index('docker tag "$source_image" "$release_image"')
    )


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
    assert 'gh pr merge "$PR_NUMBER" --auto --squash --match-head-commit "$final_head"' in workflow
    assert '--subject "$title (#${PR_NUMBER})"' in workflow
    assert 'gh api -X PUT "${pr_url}/merge"' not in workflow
    assert "merge_result" not in workflow
    assert "merge_sha" not in workflow
    assert "the PR title changed after validation" in workflow
    assert "the PR release directive changed after validation" in workflow
    assert "group_by(.context)" in workflow
    assert "gh workflow run release.yml" not in workflow
    assert "Protected squash auto-merge armed" in workflow
    assert "master-merge" in workflow
