from __future__ import annotations

import argparse
import json
import re
import secrets
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import httpx

from dojo.api.settings import get_settings
from dojo.google import (
    GOOGLE_TOKEN_URL,
    build_google_auth_url,
    fetch_sheet_named_ranges,
)
from dojo.importer import consumed_named_range_aliases, extract_sheet_id
from dojo.migrations import provision_database
from dojo.service import DojoService

DEFAULT_TOKEN_CACHE = Path("/tmp/dojo-google-sheet-token.json")
DEFAULT_AUTH_STATE_CACHE = Path("/tmp/dojo-google-sheet-auth-state.json")
DEFAULT_FETCH_DUMP = Path("/tmp/dojo-live-sheet-last-fetch.json")
DEFAULT_DUCKDB_PATH = Path("/tmp/dojo-live-sheet-harness.duckdb")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fetch and import a live Google Sheet through dojo's importer"
    )
    parser.add_argument("sheet_url_or_id")
    parser.add_argument("--token-cache", default=str(DEFAULT_TOKEN_CACHE))
    parser.add_argument("--auth-state-cache", default=str(DEFAULT_AUTH_STATE_CACHE))
    parser.add_argument("--fetch-dump", default=str(DEFAULT_FETCH_DUMP))
    parser.add_argument("--duckdb-path", default=str(DEFAULT_DUCKDB_PATH))
    parser.add_argument(
        "--authorization-response",
        help="Full callback URL copied from the browser after Google redirects back",
    )
    args = parser.parse_args()

    settings = get_settings()
    if not settings.oauth_configured:
        raise SystemExit("Google OAuth is not configured in api/.env")

    token_cache = Path(args.token_cache)
    auth_state_cache = Path(args.auth_state_cache)
    fetch_dump = Path(args.fetch_dump)
    duckdb_path = Path(args.duckdb_path)

    token = ensure_access_token(
        settings=settings,
        token_cache=token_cache,
        auth_state_cache=auth_state_cache,
        authorization_response=args.authorization_response,
    )

    access_token = token.get("access_token")
    if not isinstance(access_token, str) or not access_token.strip():
        raise SystemExit("OAuth token cache does not contain a usable access token")

    sheet_id = extract_sheet_id(args.sheet_url_or_id)
    try:
        title, available_named_ranges, named_ranges = fetch_sheet_named_ranges(
            spreadsheet_id=sheet_id,
            access_token=access_token,
            allowed_normalized_aliases=consumed_named_range_aliases(),
        )
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 401 and token.get("refresh_token"):
            token = refresh_cached_token(settings=settings, token=token, token_cache=token_cache)
            refreshed_access_token = token.get("access_token")
            if not isinstance(refreshed_access_token, str) or not refreshed_access_token.strip():
                raise
            title, available_named_ranges, named_ranges = fetch_sheet_named_ranges(
                spreadsheet_id=sheet_id,
                access_token=refreshed_access_token,
                allowed_normalized_aliases=consumed_named_range_aliases(),
            )
        else:
            raise

    fetch_dump.parent.mkdir(parents=True, exist_ok=True)
    fetch_dump.write_text(
        json.dumps(
            {
                "spreadsheet_id": sheet_id,
                "spreadsheet_title": title,
                "available_named_ranges": available_named_ranges,
                "named_ranges": named_ranges,
            },
            indent=2,
            sort_keys=True,
        )
    )

    if duckdb_path.exists():
        duckdb_path.unlink()
    duckdb_path.parent.mkdir(parents=True, exist_ok=True)

    provision_database(str(duckdb_path))
    service = DojoService(str(duckdb_path))
    try:
        result = service.import_sheet_data(
            source=args.sheet_url_or_id,
            source_kind="google_sheets",
            spreadsheet_title=title,
            named_ranges=named_ranges,
            available_named_ranges=available_named_ranges,
            expected=None,
        )
    except Exception as exc:
        print_live_import_diagnostics(exc, named_ranges)
        raise
    finally:
        service.close()

    print(
        json.dumps(
            {
                "ok": result.get("ok", True),
                "spreadsheet_id": sheet_id,
                "spreadsheet_title": title,
                "fetched_named_ranges": len(available_named_ranges),
                "duckdb_path": str(duckdb_path),
                "fetch_dump": str(fetch_dump),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def ensure_access_token(
    *,
    settings: Any,
    token_cache: Path,
    auth_state_cache: Path,
    authorization_response: str | None,
) -> dict[str, Any]:
    cached = load_json_file(token_cache)
    if cached is not None and token_is_fresh(cached):
        return cached
    if cached is not None and cached.get("refresh_token"):
        return refresh_cached_token(settings=settings, token=cached, token_cache=token_cache)
    if authorization_response is not None:
        token = exchange_authorization_response(
            settings=settings,
            auth_state_cache=auth_state_cache,
            authorization_response=authorization_response,
        )
        write_json_file(token_cache, token)
        return token

    state = secrets.token_urlsafe(24)
    write_json_file(auth_state_cache, {"state": state, "created_at": utc_now_iso()})
    auth_url = build_google_auth_url(
        client_id=settings.google_oauth_client_id,
        redirect_uri=settings.google_oauth_redirect_uri,
        scopes=settings.google_oauth_scopes,
        state=state,
    )
    raise SystemExit(
        "No cached Google token is available.\n"
        "1. Open this URL in a browser and complete Google auth:\n"
        f"{auth_url}\n"
        "2. If your local API is running on the OAuth callback URL, stop it first so the code is not consumed.\n"
        "3. After Google redirects back to localhost, copy the full callback URL from the browser address bar.\n"
        "4. Re-run this command with --authorization-response '<callback-url>'."
    )


def exchange_authorization_response(
    *, settings: Any, auth_state_cache: Path, authorization_response: str
) -> dict[str, Any]:
    cached_state = load_json_file(auth_state_cache)
    if cached_state is None or not isinstance(cached_state.get("state"), str):
        raise SystemExit(
            "No pending OAuth state was found; run the harness once without a token first"
        )

    parsed = urlparse(authorization_response.strip())
    query = parse_qs(parsed.query)
    code = first_query_value(query, "code")
    state = first_query_value(query, "state")
    if code is None or state is None:
        raise SystemExit("Authorization response must include both code and state query parameters")
    if state != cached_state["state"]:
        raise SystemExit("Authorization response state does not match the pending harness state")

    response = httpx.post(
        GOOGLE_TOKEN_URL,
        data={
            "code": code,
            "client_id": settings.google_oauth_client_id,
            "client_secret": settings.google_oauth_client_secret,
            "redirect_uri": settings.google_oauth_redirect_uri,
            "grant_type": "authorization_code",
        },
        timeout=30.0,
    )
    response.raise_for_status()
    token = dict(response.json())
    token["obtained_at"] = utc_now_iso()
    return token


def refresh_cached_token(
    *, settings: Any, token: dict[str, Any], token_cache: Path
) -> dict[str, Any]:
    refresh_token = token.get("refresh_token")
    if not isinstance(refresh_token, str) or not refresh_token.strip():
        return token
    response = httpx.post(
        GOOGLE_TOKEN_URL,
        data={
            "client_id": settings.google_oauth_client_id,
            "client_secret": settings.google_oauth_client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=30.0,
    )
    response.raise_for_status()
    refreshed = dict(token)
    refreshed.update(dict(response.json()))
    refreshed["refresh_token"] = refresh_token
    refreshed["obtained_at"] = utc_now_iso()
    write_json_file(token_cache, refreshed)
    return refreshed


def token_is_fresh(token: dict[str, Any]) -> bool:
    access_token = token.get("access_token")
    expires_in = token.get("expires_in")
    obtained_at = token.get("obtained_at")
    if not isinstance(access_token, str) or not access_token.strip():
        return False
    if not isinstance(expires_in, int) or not isinstance(obtained_at, str):
        return True
    issued_at = datetime.fromisoformat(obtained_at)
    expires_at = issued_at + timedelta(seconds=expires_in)
    return expires_at - timedelta(minutes=5) > datetime.now(UTC)


def print_live_import_diagnostics(exc: Exception, named_ranges: dict[str, list[list[str]]]) -> None:
    message = str(exc)
    print(f"Import failed: {message}")
    row_match = re.search(r"row (\d+)", message)
    if row_match is None:
        return
    row_index = int(row_match.group(1)) - 1
    if "transaction" in message.casefold():
        print(
            json.dumps(
                {
                    "transaction_row_number": row_index + 1,
                    "date": value_at(named_ranges, "trx_Dates", row_index),
                    "outflow": value_at(named_ranges, "trx_Outflows", row_index),
                    "inflow": value_at(named_ranges, "trx_Inflows", row_index),
                    "category": value_at(named_ranges, "trx_Categories", row_index),
                    "account": value_at(named_ranges, "trx_Accounts", row_index),
                    "memo": value_at(named_ranges, "trx_Memos", row_index),
                    "status": value_at(named_ranges, "trx_Statuses", row_index),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return
    if "category row" in message.casefold():
        print(
            json.dumps(
                {
                    "category_row_number": row_index + 1,
                    "name": value_at(named_ranges, "UserDefCategories", row_index),
                    "amount": value_at(named_ranges, "UserDefAmounts", row_index),
                    "goal": value_at(named_ranges, "UserDefGoals", row_index),
                    "linked_account": value_at(named_ranges, "UserDefLinkedAccounts", row_index),
                },
                indent=2,
                sort_keys=True,
            )
        )


def value_at(
    named_ranges: dict[str, list[list[str]]], range_name: str, row_index: int
) -> str | None:
    rows = named_ranges.get(range_name)
    if rows is None or row_index < 0 or row_index >= len(rows):
        return None
    row = rows[row_index]
    if not row:
        return ""
    return str(row[0])


def first_query_value(query: dict[str, list[str]], key: str) -> str | None:
    values = query.get(key)
    if not values:
        return None
    value = values[0].strip()
    return value or None


def load_json_file(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text())
    if not isinstance(payload, dict):
        raise ValueError(f"JSON file {path} does not contain an object")
    return payload


def write_json_file(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True))


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
