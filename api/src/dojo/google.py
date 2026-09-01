from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import Any, cast

import httpx
from authlib.integrations.httpx_client import OAuth2Client  # type: ignore[import-untyped]
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_SHEETS_BASE_URL = "https://sheets.googleapis.com/v4/spreadsheets"

MAX_RETRIES = 3


def _is_transient_error(exc: BaseException) -> bool:
    """Retry on connection errors and 5xx; do NOT retry 401/403."""
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code >= 500
    return isinstance(exc, httpx.TransportError)


_TRANSIENT_RETRY = retry(
    retry=retry_if_exception(_is_transient_error),
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=0.5, max=10),
    reraise=True,
)


def build_google_auth_url(
    *,
    client_id: str,
    redirect_uri: str,
    scopes: str,
    state: str,
) -> str:
    client = OAuth2Client(
        client_id=client_id,
        redirect_uri=redirect_uri,
        scope=scopes,
        token_endpoint=GOOGLE_TOKEN_URL,
    )
    url, _state = client.create_authorization_url(
        GOOGLE_AUTH_URL,
        state=state,
        response_type="code",
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        login_hint="",
    )
    return str(url)


@_TRANSIENT_RETRY
def exchange_google_code(
    *,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    code: str,
) -> dict[str, Any]:
    client = OAuth2Client(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        token_endpoint=GOOGLE_TOKEN_URL,
    )
    authorization_response = f"{redirect_uri}?code={code}&state="
    token = client.fetch_token(
        GOOGLE_TOKEN_URL,
        authorization_response=authorization_response,
    )
    return dict(token)


@dataclass(frozen=True)
class PendingOAuthAuthorization:
    session_id: str
    frontend_origin: str


class OAuthTokenStore:
    def __init__(self) -> None:
        self._tokens_by_session_id: dict[str, dict[str, Any]] = {}
        self._pending_by_state: dict[str, PendingOAuthAuthorization] = {}
        self._lock = RLock()

    def begin_authorization(self, *, state: str, session_id: str, frontend_origin: str) -> None:
        with self._lock:
            self._pending_by_state[state] = PendingOAuthAuthorization(
                session_id=session_id,
                frontend_origin=frontend_origin,
            )

    def consume_authorization(self, state: str) -> PendingOAuthAuthorization | None:
        with self._lock:
            return self._pending_by_state.pop(state, None)

    def set(self, session_id: str, token: dict[str, Any]) -> None:
        with self._lock:
            self._tokens_by_session_id[session_id] = token

    def get(self, session_id: str) -> dict[str, Any] | None:
        with self._lock:
            token = self._tokens_by_session_id.get(session_id)
            if token is None:
                return None
            return dict(token)

    def has(self, session_id: str) -> bool:
        with self._lock:
            return session_id in self._tokens_by_session_id

    def clear(self, session_id: str) -> None:
        with self._lock:
            self._tokens_by_session_id.pop(session_id, None)


@_TRANSIENT_RETRY
def fetch_sheet_named_ranges(
    *, spreadsheet_id: str, access_token: str, allowed_normalized_aliases: set[str]
) -> tuple[str, list[str], dict[str, list[list[str]]]]:
    headers = {"Authorization": f"Bearer {access_token}"}
    metadata = httpx.get(
        f"{GOOGLE_SHEETS_BASE_URL}/{spreadsheet_id}",
        params={"fields": "properties.title,namedRanges(name,range)"},
        headers=headers,
        timeout=30.0,
    )
    metadata.raise_for_status()
    metadata_payload = cast(dict[str, Any], metadata.json())
    title = cast(str, metadata_payload.get("properties", {}).get("title", spreadsheet_id))
    all_named_range_metadata = cast(list[dict[str, Any]], metadata_payload.get("namedRanges", []))
    named_range_metadata = [
        item
        for item in all_named_range_metadata
        if _normalize_name(cast(str, item["name"])) in allowed_normalized_aliases
    ]
    named_range_names = [cast(str, item["name"]) for item in named_range_metadata]

    if not named_range_names:
        return title, [], {}

    params: tuple[tuple[str, str | int | float | bool | None], ...] = tuple(
        ("ranges", name) for name in named_range_names
    )
    response = httpx.get(
        f"{GOOGLE_SHEETS_BASE_URL}/{spreadsheet_id}/values:batchGet",
        params=params,
        headers=headers,
        timeout=30.0,
    )
    response.raise_for_status()
    value_ranges = cast(list[dict[str, Any]], response.json().get("valueRanges", []))

    named_ranges: dict[str, list[list[str]]] = {}
    for index, name in enumerate(named_range_names):
        grid_range = cast(dict[str, int], named_range_metadata[index].get("range", {}))
        expected_rows = _row_count_from_grid_range(grid_range)
        expected_columns = _column_count_from_grid_range(grid_range)
        value_range = value_ranges[index] if index < len(value_ranges) else {}
        named_ranges[name] = _rectangularize_values(
            cast(list[list[Any]], value_range.get("values", [])),
            expected_rows=expected_rows,
            expected_columns=expected_columns,
            range_name=name,
        )

    return title, named_range_names, named_ranges


def _row_count_from_grid_range(grid_range: dict[str, int]) -> int:
    start = int(grid_range.get("startRowIndex", 0))
    end = int(grid_range.get("endRowIndex", start))
    return max(0, end - start)


def _normalize_name(name: str) -> str:
    return "".join(character for character in name.casefold() if character.isalnum())


def _column_count_from_grid_range(grid_range: dict[str, int]) -> int:
    start = int(grid_range.get("startColumnIndex", 0))
    end = int(grid_range.get("endColumnIndex", start))
    return max(0, end - start)


def _rectangularize_values(
    values: list[list[Any]],
    *,
    expected_rows: int,
    expected_columns: int,
    range_name: str,
) -> list[list[str]]:
    normalized: list[list[str]] = []
    for row in values:
        normalized.append([str(cell) for cell in row])

    if expected_columns == 0:
        expected_columns = max((len(row) for row in normalized), default=0)

    rectangular = [
        row[:expected_columns] + [""] * max(0, expected_columns - len(row)) for row in normalized
    ]
    if len(rectangular) < expected_rows:
        rectangular.extend(
            [[""] * expected_columns for _ in range(expected_rows - len(rectangular))]
        )
    if not rectangular and expected_rows > 0:
        rectangular = [[""] * expected_columns for _ in range(expected_rows)]
    if expected_columns == 0 and rectangular:
        raise ValueError(f"Named range {range_name} resolved to zero columns")
    return rectangular[:expected_rows]
