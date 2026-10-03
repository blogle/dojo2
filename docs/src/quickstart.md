# Quickstart

1. Install Nix and direnv.
2. Run `direnv allow` in the repository root.
3. Run `just setup`.
4. Start the API with `just dev-api`.
5. Start the web app with `just dev-web`.
6. To explore representative sample data, run `just dev-fixture`, then start the API with `DUCKDB_PATH=.local/dev-fixture.duckdb just api` (the file lives at `api/.local/dev-fixture.duckdb`). This generated database is independent of the normal empty-database onboarding flow; rerun the generator to reset it.
7. When Google OAuth credentials are configured, use the same onboarding flow with a copied Google Sheet URL or ID instead.
8. Verify the project with `just lint`, `just typecheck`, `just test`, and `just docs`.
