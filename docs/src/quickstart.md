# Quickstart

1. Install Nix and direnv.
2. Run `direnv allow` in the repository root.
3. Run `just setup`.
4. Start the API with `just dev-api`.
5. Start the web app with `just dev-web`.
6. Open the web app and, on a fresh database, use `fixture://default` on the onboarding screen.
7. When Google OAuth credentials are configured, use the same onboarding flow with a copied Google Sheet URL or ID instead.
8. Verify the project with `just lint`, `just typecheck`, `just test`, and `just docs`.
