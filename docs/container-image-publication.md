# Container image publication

The CI publisher stores provenance-neutral runtime and web content under
`content-<git-tree-sha>`, then creates the immutable deployable
`git-<commit-sha>` image as a metadata-only wrapper. The tree tag identifies
content; it does not claim to identify a commit. Deployable images carry the
exact commit in `DOJO_BUILD_SHA` and `org.opencontainers.image.revision`.

For a squash publication miss before this change, staging rebuilt the web
assets, built a commit-SHA-parameterized Nix image, then built and pushed the
Docker image. For a same-tree squash publication after this change, staging
pulls the existing tree image, builds only the metadata wrapper, and pushes
the exact master `git-<commit-sha>` image. No elapsed-time comparison is
claimed. The deterministic publisher test confirms that a same-tree content
hit pulls the existing content artifact and skips both `just build-web` and
`nix build .#container`.

Live verification still requires merge and publication privileges. After
squash-merging this PR, verify that the master workflow publishes
`git-<master-sha>` from the existing `content-<tree-sha>` artifact, and inspect
that image to confirm both `DOJO_BUILD_SHA` and
`org.opencontainers.image.revision` equal the resulting master SHA. Confirm
that staging points to that exact immutable image. Then verify a delayed
publication for an older master commit leaves staging unchanged, and confirm
the versioned release image is promoted from the exact master immutable
artifact. Record actual before/after build timings only if those live runs
provide comparable measurements.
