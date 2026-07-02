from __future__ import annotations

from typing import Any
from unittest.mock import patch

import httpx
import pytest

from dojo.google import (
    _is_transient_error,
    build_google_auth_url,
    exchange_google_code,
    fetch_sheet_named_ranges,
)


def _make_response(status_code: int, json_data: dict[str, Any] | None = None) -> httpx.Response:
    response = httpx.Response(
        status_code=status_code,
        json=json_data or {},
        request=httpx.Request("GET", "https://example.com"),
    )
    return response


def _make_status_error(status_code: int) -> httpx.HTTPStatusError:
    response = _make_response(status_code)
    return httpx.HTTPStatusError(
        message=f"{status_code} Error",
        request=response.request,
        response=response,
    )


class TestIsTransientError:
    def test_returns_true_for_500(self) -> None:
        assert _is_transient_error(_make_status_error(500)) is True

    def test_returns_true_for_503(self) -> None:
        assert _is_transient_error(_make_status_error(503)) is True

    def test_returns_false_for_401(self) -> None:
        assert _is_transient_error(_make_status_error(401)) is False

    def test_returns_false_for_403(self) -> None:
        assert _is_transient_error(_make_status_error(403)) is False

    def test_returns_false_for_429(self) -> None:
        assert _is_transient_error(_make_status_error(429)) is False

    def test_returns_true_for_connect_error(self) -> None:
        assert _is_transient_error(httpx.ConnectError("refused")) is True

    def test_returns_true_for_read_timeout(self) -> None:
        assert _is_transient_error(httpx.ReadTimeout("timeout")) is True

    def test_returns_false_for_unrelated_exception(self) -> None:
        assert _is_transient_error(ValueError("nope")) is False


class TestBuildGoogleAuthUrl:
    def test_returns_url_with_expected_params(self) -> None:
        url = build_google_auth_url(
            client_id="test-id",
            redirect_uri="http://localhost/callback",
            scopes="https://www.googleapis.com/auth/spreadsheets.readonly",
            state="mystate",
        )
        assert "accounts.google.com" in url
        assert "client_id=test-id" in url
        assert "response_type=code" in url
        assert "access_type=offline" in url
        assert "prompt=consent" in url
        assert "state=mystate" in url


class TestExchangeGoogleCode:
    def test_returns_token_dict(self) -> None:
        token_response = {
            "access_token": "ya29.access",
            "refresh_token": "1//refresh",
            "token_type": "Bearer",
            "expires_in": 3600,
        }

        with patch("dojo.google.OAuth2Client") as MockClient:
            instance = MockClient.return_value
            instance.fetch_token.return_value = token_response

            result = exchange_google_code(
                client_id="id",
                client_secret="secret",
                redirect_uri="http://localhost/cb",
                code="auth_code",
            )

            assert result["access_token"] == "ya29.access"
            assert result["refresh_token"] == "1//refresh"
            instance.fetch_token.assert_called_once()

    def test_retries_on_transient_httpx_error(self) -> None:
        token_response = {"access_token": "recovered", "token_type": "Bearer"}

        with patch("dojo.google.OAuth2Client") as MockClient:
            instance = MockClient.return_value
            instance.fetch_token.side_effect = [
                httpx.ConnectError("connection refused"),
                token_response,
            ]

            result = exchange_google_code(
                client_id="id",
                client_secret="secret",
                redirect_uri="http://localhost/cb",
                code="auth_code",
            )

            assert result["access_token"] == "recovered"
            assert instance.fetch_token.call_count == 2

    def test_no_retry_on_401(self) -> None:
        with patch("dojo.google.OAuth2Client") as MockClient:
            instance = MockClient.return_value
            instance.fetch_token.side_effect = _make_status_error(401)

            with pytest.raises(httpx.HTTPStatusError) as exc_info:
                exchange_google_code(
                    client_id="id",
                    client_secret="secret",
                    redirect_uri="http://localhost/cb",
                    code="auth_code",
                )
            assert exc_info.value.response.status_code == 401
            assert instance.fetch_token.call_count == 1

    def test_no_retry_on_403(self) -> None:
        with patch("dojo.google.OAuth2Client") as MockClient:
            instance = MockClient.return_value
            instance.fetch_token.side_effect = _make_status_error(403)

            with pytest.raises(httpx.HTTPStatusError):
                exchange_google_code(
                    client_id="id",
                    client_secret="secret",
                    redirect_uri="http://localhost/cb",
                    code="auth_code",
                )
            assert instance.fetch_token.call_count == 1


class TestFetchSheetNamedRanges:
    def test_returns_title_and_ranges(self) -> None:
        metadata_payload = {
            "properties": {"title": "My Sheet"},
            "namedRanges": [
                {
                    "name": "trx_Dates",
                    "range": {
                        "startRowIndex": 0,
                        "endRowIndex": 2,
                        "startColumnIndex": 0,
                        "endColumnIndex": 1,
                    },
                },
            ],
        }
        values_payload = {
            "valueRanges": [
                {"values": [["2024-01-01"], ["2024-01-02"]]},
            ],
        }

        def mock_get(url: str, **kwargs: Any) -> httpx.Response:
            if "batchGet" in url:
                return _make_response(200, values_payload)
            return _make_response(200, metadata_payload)

        with patch("dojo.google.httpx.get", side_effect=mock_get):
            title, names, ranges = fetch_sheet_named_ranges(
                spreadsheet_id="sheet123",
                access_token="token",
                allowed_normalized_aliases={"trxdates"},
            )

        assert title == "My Sheet"
        assert names == ["trx_Dates"]
        assert "trx_Dates" in ranges
        assert ranges["trx_Dates"] == [["2024-01-01"], ["2024-01-02"]]

    def test_retries_on_500_then_succeeds(self) -> None:
        metadata_payload = {
            "properties": {"title": "Sheet"},
            "namedRanges": [],
        }

        call_count = 0

        def mock_get(url: str, **kwargs: Any) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise _make_status_error(500)
            return _make_response(200, metadata_payload)

        with patch("dojo.google.httpx.get", side_effect=mock_get):
            title, names, ranges = fetch_sheet_named_ranges(
                spreadsheet_id="sheet123",
                access_token="token",
                allowed_normalized_aliases=set(),
            )

        assert title == "Sheet"
        assert call_count == 2

    def test_no_retry_on_401(self) -> None:
        def mock_get(url: str, **kwargs: Any) -> httpx.Response:
            raise _make_status_error(401)

        with patch("dojo.google.httpx.get", side_effect=mock_get):
            with pytest.raises(httpx.HTTPStatusError) as exc_info:
                fetch_sheet_named_ranges(
                    spreadsheet_id="sheet123",
                    access_token="bad_token",
                    allowed_normalized_aliases=set(),
                )
            assert exc_info.value.response.status_code == 401

    def test_retries_on_connect_error(self) -> None:
        metadata_payload = {
            "properties": {"title": "Sheet"},
            "namedRanges": [],
        }

        call_count = 0

        def mock_get(url: str, **kwargs: Any) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise httpx.ConnectError("connection refused")
            return _make_response(200, metadata_payload)

        with patch("dojo.google.httpx.get", side_effect=mock_get):
            title, _, _ = fetch_sheet_named_ranges(
                spreadsheet_id="sheet123",
                access_token="token",
                allowed_normalized_aliases=set(),
            )

        assert title == "Sheet"
        assert call_count == 2


class TestOAuthTokenStore:
    def test_set_and_get(self) -> None:
        from dojo.google import OAuthTokenStore

        store = OAuthTokenStore()
        store.set("s1", {"access_token": "tok"})
        assert store.get("s1") == {"access_token": "tok"}

    def test_get_returns_copy(self) -> None:
        from dojo.google import OAuthTokenStore

        store = OAuthTokenStore()
        store.set("s1", {"access_token": "tok"})
        token = store.get("s1")
        token["access_token"] = "mutated"
        assert store.get("s1") == {"access_token": "tok"}

    def test_has_and_clear(self) -> None:
        from dojo.google import OAuthTokenStore

        store = OAuthTokenStore()
        assert store.has("s1") is False
        store.set("s1", {"access_token": "tok"})
        assert store.has("s1") is True
        store.clear("s1")
        assert store.has("s1") is False

    def test_get_missing_returns_none(self) -> None:
        from dojo.google import OAuthTokenStore

        store = OAuthTokenStore()
        assert store.get("nonexistent") is None
