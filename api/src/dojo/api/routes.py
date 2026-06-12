from __future__ import annotations

import secrets
from typing import Any, cast

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse

from dojo.api.models import (
    AccountPayload,
    AccountUpdatePayload,
    AllocationRequest,
    CategoryGroupPayload,
    CategoryGroupUpdatePayload,
    CategoryPayload,
    CategoryUpdatePayload,
    ImportRequest,
    TransactionPayload,
    TransferPayload,
)
from dojo.api.settings import Settings
from dojo.google import (
    OAuthTokenStore,
    build_google_auth_url,
    exchange_google_code,
    fetch_sheet_named_ranges,
)
from dojo.importer import consumed_named_range_aliases, extract_sheet_id
from dojo.service import DojoService

router = APIRouter(prefix="/api")


def get_service(request: Request) -> DojoService:
    return cast(DojoService, request.app.state.dojo_service)


def get_settings(request: Request) -> Settings:
    return cast(Settings, request.app.state.settings)


def get_oauth_token_store(request: Request) -> OAuthTokenStore:
    return cast(OAuthTokenStore, request.app.state.oauth_token_store)


def get_or_create_oauth_session_id(request: Request) -> str:
    session_id = cast(str | None, request.session.get("google_oauth_session_id"))
    if session_id:
        return session_id
    session_id = secrets.token_urlsafe(24)
    request.session["google_oauth_session_id"] = session_id
    return session_id


def oauth_status_payload(request: Request) -> dict[str, Any]:
    settings = get_settings(request)
    session_id = get_or_create_oauth_session_id(request)
    token_store = get_oauth_token_store(request)
    return {
        "configured": settings.oauth_configured,
        "fixture_mode": settings.dev_fixture_mode,
        "authorized": token_store.has(session_id),
        "message": (
            "Google OAuth is configured and ready."
            if settings.oauth_configured
            else "Google OAuth is not configured in this environment."
        ),
    }


@router.get("/app/status")
def app_status(request: Request) -> dict[str, Any]:
    return get_service(request).get_app_status()


@router.post("/onboarding/google/start")
def start_google_onboarding(request: Request) -> dict[str, Any]:
    settings = get_settings(request)
    payload = oauth_status_payload(request)
    if not settings.oauth_configured:
        return payload | {"auth_url": None}
    state = secrets.token_urlsafe(24)
    request.session["google_oauth_state"] = state
    return payload | {
        "auth_url": build_google_auth_url(
            client_id=settings.google_oauth_client_id,
            redirect_uri=settings.google_oauth_redirect_uri,
            scopes=settings.google_oauth_scopes,
            state=state,
        ),
    }


@router.get("/onboarding/google/status")
def google_onboarding_status(request: Request) -> dict[str, Any]:
    return oauth_status_payload(request)


@router.get("/onboarding/google/callback")
def google_callback(request: Request, code: str, state: str) -> HTMLResponse:
    settings = get_settings(request)
    if request.session.get("google_oauth_state") != state:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")
    token = exchange_google_code(
        client_id=settings.google_oauth_client_id,
        client_secret=settings.google_oauth_client_secret,
        redirect_uri=settings.google_oauth_redirect_uri,
        code=code,
    )
    session_id = get_or_create_oauth_session_id(request)
    get_oauth_token_store(request).set(session_id, token)
    return HTMLResponse(
        f"<html><body><script>window.opener?.postMessage({{type:'dojo-google-oauth',ok:true}}, {settings.frontend_base_url!r});window.close();</script>Google access granted.</body></html>"
    )


@router.post("/import/google-sheet")
def import_google_sheet(request: Request, payload: ImportRequest) -> dict[str, Any]:
    settings = get_settings(request)
    service = get_service(request)
    raw = payload.sheet_url_or_id
    normalized = raw.strip().casefold()
    if normalized in {"fixture", "fixture://default", "default"} or (
        settings.dev_fixture_mode and not settings.oauth_configured
    ):
        return service.import_sheet_data(source="fixture://default", source_kind="fixture")

    session_id = get_or_create_oauth_session_id(request)
    token = get_oauth_token_store(request).get(session_id)
    if token is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "Google Sheets access has not been granted for this browser session. "
                "Complete the OAuth step and try again."
            ),
        )
    access_token = token.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=400,
            detail="Google OAuth succeeded, but this session does not have a usable access token.",
        )
    try:
        spreadsheet_id = extract_sheet_id(raw)
        title, available_named_ranges, named_ranges = fetch_sheet_named_ranges(
            spreadsheet_id=spreadsheet_id,
            access_token=cast(str, access_token),
            allowed_normalized_aliases=consumed_named_range_aliases(),
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to fetch Google Sheet: {exc}") from exc
    return service.import_sheet_data(
        source=raw,
        source_kind="google_sheets",
        spreadsheet_title=title,
        named_ranges=named_ranges,
        available_named_ranges=available_named_ranges,
        expected=None,
    )


@router.get("/import/status")
def import_status(request: Request) -> dict[str, Any]:
    return {
        "latest_run": get_service(request).get_import_status(),
        "app_status": get_service(request).get_app_status(),
    }


@router.get("/bootstrap")
def bootstrap(request: Request) -> dict[str, Any]:
    return get_service(request).get_bootstrap()


@router.get("/budget")
def budget(request: Request, month: str | None = None, show_hidden: bool = False) -> dict[str, Any]:
    service = get_service(request)
    return service.get_budget(month or service.default_budget_month(), show_hidden=show_hidden)


@router.post("/allocations/fund")
def fund_category(request: Request, payload: AllocationRequest) -> dict[str, Any]:
    return get_service(request).create_allocation(
        from_bucket_id=payload.from_bucket_id,
        to_bucket_id=payload.to_bucket_id,
        amount_minor=payload.amount_minor,
        memo=payload.memo,
        allocation_date=payload.date,
    )


@router.post("/allocations/move")
def move_money(request: Request, payload: AllocationRequest) -> dict[str, Any]:
    return fund_category(request, payload)


@router.post("/allocations/return-to-atb")
def return_to_atb(request: Request, payload: AllocationRequest) -> dict[str, Any]:
    return fund_category(request, payload)


@router.get("/transactions")
def transactions(
    request: Request,
    limit: int = Query(default=500, ge=1, le=10_000),
    show_hidden: bool = False,
) -> dict[str, Any]:
    return {"items": get_service(request).list_transactions(limit=limit, show_hidden=show_hidden)}


@router.post("/transactions")
def create_transaction(request: Request, payload: TransactionPayload) -> dict[str, Any]:
    return get_service(request).create_transaction(payload.model_dump())


@router.put("/transactions/{transaction_id}")
def update_transaction(
    request: Request, transaction_id: str, payload: TransactionPayload
) -> dict[str, Any]:
    return get_service(request).update_transaction(transaction_id, payload.model_dump())


@router.delete("/transactions/{transaction_id}")
def delete_transaction(request: Request, transaction_id: str) -> dict[str, Any]:
    get_service(request).delete_transaction(transaction_id)
    return {"ok": True}


@router.post("/transfers")
def create_transfer(request: Request, payload: TransferPayload) -> dict[str, Any]:
    return get_service(request).create_transfer(
        from_account_id=payload.from_account_id,
        to_account_id=payload.to_account_id,
        amount_minor=payload.amount_minor,
        transfer_date=payload.date,
        memo=payload.memo,
        status=payload.status,
    )


@router.get("/accounts")
def accounts(request: Request, show_hidden: bool = False) -> dict[str, Any]:
    return {"items": get_service(request).list_accounts(show_hidden=show_hidden)}


@router.post("/accounts")
def create_account(request: Request, payload: AccountPayload) -> dict[str, Any]:
    return get_service(request).create_account(payload.model_dump())


@router.put("/accounts/{account_id}")
def update_account(
    request: Request, account_id: str, payload: AccountUpdatePayload
) -> dict[str, Any]:
    return get_service(request).update_account(account_id, payload.model_dump(exclude_none=True))


@router.get("/categories")
def categories(
    request: Request, month: str | None = None, show_hidden: bool = False
) -> dict[str, Any]:
    service = get_service(request)
    active_month = month or service.default_budget_month()
    return {
        "groups": service.list_category_groups(month=active_month, show_hidden=show_hidden),
        "items": service.list_categories(month=active_month, show_hidden=show_hidden),
    }


@router.post("/category-groups")
def create_category_group(request: Request, payload: CategoryGroupPayload) -> dict[str, Any]:
    return get_service(request).create_category_group(payload.model_dump())


@router.put("/category-groups/{group_id}")
def update_category_group(
    request: Request, group_id: str, payload: CategoryGroupUpdatePayload
) -> dict[str, Any]:
    return get_service(request).update_category_group(
        group_id, payload.model_dump(exclude_none=True)
    )


@router.post("/categories")
def create_category(request: Request, payload: CategoryPayload) -> dict[str, Any]:
    return get_service(request).create_category(payload.model_dump())


@router.put("/categories/{category_id}")
def update_category(
    request: Request, category_id: str, payload: CategoryUpdatePayload
) -> dict[str, Any]:
    return get_service(request).update_category(category_id, payload.model_dump(exclude_none=True))


@router.get("/net-worth")
def net_worth(request: Request) -> dict[str, Any]:
    return get_service(request).get_net_worth()
