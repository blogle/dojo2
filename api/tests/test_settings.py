from dojo.api.settings import Settings


def test_settings_load_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("APP_BASE_URL", "http://localhost:5173")
    monkeypatch.setenv("API_BASE_URL", "http://localhost:8000")
    monkeypatch.setenv("FRONTEND_BASE_URL", "http://localhost:5173")
    monkeypatch.setenv("DUCKDB_PATH", ".local/test.duckdb")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "client-id")
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "client-secret")
    monkeypatch.setenv(
        "GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8000/api/onboarding/google/callback"
    )
    monkeypatch.setenv(
        "GOOGLE_OAUTH_SCOPES", "https://www.googleapis.com/auth/spreadsheets.readonly"
    )
    monkeypatch.setenv("SESSION_SECRET", "secret")
    monkeypatch.setenv("DEV_FIXTURE_MODE", "true")

    settings = Settings()

    assert settings.app_env == "test"
    assert settings.duckdb_path == ".local/test.duckdb"
    assert settings.google_oauth_client_id == "client-id"
    assert settings.google_oauth_client_secret == "client-secret"
    assert (
        settings.google_oauth_redirect_uri == "http://localhost:8000/api/onboarding/google/callback"
    )
    assert settings.session_secret == "secret"
    assert settings.dev_fixture_mode is True
    assert settings.oauth_configured is True
