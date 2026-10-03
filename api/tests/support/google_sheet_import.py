from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

import dojo.api.routes as routes_module
from dojo.constants import GOOGLE_SHEETS_READONLY_SCOPE
from dojo.fixture_data import DEFAULT_FIXTURE
from dojo.google import DOJO_GRANTED_SCOPES_KEY

TEST_SPREADSHEET_ID = "synthetic-test-spreadsheet"
TEST_SPREADSHEET_TITLE = "Synthetic importer test workbook"


def _named_ranges() -> dict[str, list[list[str]]]:
    return DEFAULT_FIXTURE["named_ranges"]


def seed_service_from_test_workbook(service) -> dict[str, Any]:
    return service.import_sheet_data(
        source=TEST_SPREADSHEET_ID,
        source_kind="google_sheets",
        spreadsheet_title=TEST_SPREADSHEET_TITLE,
        named_ranges=_named_ranges(),
    )


class AuthorizedTestTokenStore:
    def get(self, _session_id: str) -> dict[str, Any]:
        return {
            "access_token": "synthetic-test-access-token",
            DOJO_GRANTED_SCOPES_KEY: (GOOGLE_SHEETS_READONLY_SCOPE,),
        }


def configure_sheet_import(monkeypatch) -> None:
    named_ranges = _named_ranges()

    monkeypatch.setattr(
        routes_module,
        "get_oauth_token_store",
        lambda _request: AuthorizedTestTokenStore(),
    )
    monkeypatch.setattr(
        routes_module,
        "_fetch_google_sheet_named_ranges",
        lambda _request, **_kwargs: (
            TEST_SPREADSHEET_TITLE,
            list(named_ranges),
            named_ranges,
        ),
    )


def import_test_sheet(client: TestClient, monkeypatch) -> Any:
    configure_sheet_import(monkeypatch)
    return client.post("/api/import/google-sheet", json={"sheet_url_or_id": TEST_SPREADSHEET_ID})


def analyze_test_sheet(client: TestClient, monkeypatch) -> Any:
    configure_sheet_import(monkeypatch)
    return client.post(
        "/api/import/google-sheet/analyze", json={"sheet_url_or_id": TEST_SPREADSHEET_ID}
    )
