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
claimed; live PR-to-squash-to-staging verification requires the supervising
thread's merge and publication privileges.
