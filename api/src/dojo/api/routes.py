from __future__ import annotations

import secrets
from typing import Any, cast

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse

from dojo.api.models import (
    AccountBudgetLinkPayload,
    AccountPayload,
    AccountUpdatePayload,
    AllocationRequest,
    CategoryGroupPayload,
    CategoryGroupUpdatePayload,
    CategoryPayload,
    CategoryUpdatePayload,
    CreditCardPaymentPayload,
    FundCategoryRequest,
    GoalPayload,
    ImportCommitRequest,
    ImportRequest,
    InvestmentCashSnapshotPayload,
    InvestmentPositionPayload,
    InvestmentPriceSnapshotPayload,
    InvestmentStatementPayload,
    InvestmentTransferPayload,
    LoanBalanceSnapshotPayload,
    LoanPaymentPayload,
    ReconciliationApplyPayload,
    ReconciliationDraftPayload,
    TangibleAssetValuationPayload,
    TrackingAccountSnapshotPayload,
    TrackingCutoverPayload,
    TransactionPayload,
    TransferPayload,
)
from dojo.api.settings import Settings
from dojo.commands import CommandConflictError
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


@router.post("/import/google-sheet/analyze")
def analyze_google_sheet(request: Request, payload: ImportRequest) -> dict[str, Any]:
    settings = get_settings(request)
    service = get_service(request)
    raw = payload.sheet_url_or_id
    normalized = raw.strip().casefold()
    if normalized in {"fixture", "fixture://default", "default"} or (
        settings.dev_fixture_mode and not settings.oauth_configured
    ):
        return service.analyze_import_draft(source="fixture://default", source_kind="fixture")

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
    return service.analyze_import_draft(
        source=raw,
        source_kind="google_sheets",
        spreadsheet_title=title,
        named_ranges=named_ranges,
        available_named_ranges=available_named_ranges,
        expected=None,
    )


@router.post("/import/google-sheet/commit")
def commit_google_sheet_import(request: Request, payload: ImportCommitRequest) -> dict[str, Any]:
    service = get_service(request)
    try:
        return service.commit_import_draft(
            draft_id=payload.draft_id,
            decisions=[d.model_dump() for d in payload.decisions],
            low_confidence_confirmed=payload.low_confidence_confirmed,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/bootstrap")
def bootstrap(request: Request) -> dict[str, Any]:
    return get_service(request).get_bootstrap()


@router.get("/budget")
def budget(
    request: Request, *, month: str | None = None, show_hidden: bool = False
) -> dict[str, Any]:
    service = get_service(request)
    return service.get_budget(month or service.default_budget_month(), show_hidden=show_hidden)


@router.post("/allocations/fund")
def fund_category(request: Request, payload: FundCategoryRequest) -> dict[str, Any]:
    try:
        return get_service(request).fund_category(
            client_operation_id=str(payload.client_operation_id),
            category_id=payload.category_id,
            amount_minor=payload.amount_minor,
            memo=payload.memo,
            allocation_date=payload.date,
        )
    except CommandConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/allocations/move")
def move_money(request: Request, payload: AllocationRequest) -> dict[str, Any]:
    return get_service(request).create_allocation(
        from_bucket_id=payload.from_bucket_id,
        to_bucket_id=payload.to_bucket_id,
        amount_minor=payload.amount_minor,
        memo=payload.memo,
        allocation_date=payload.date,
    )


@router.post("/allocations/return-to-atb")
def return_to_atb(request: Request, payload: AllocationRequest) -> dict[str, Any]:
    return get_service(request).create_allocation(
        from_bucket_id=payload.from_bucket_id,
        to_bucket_id=payload.to_bucket_id,
        amount_minor=payload.amount_minor,
        memo=payload.memo,
        allocation_date=payload.date,
    )


@router.get("/allocations")
def allocations(request: Request, *, show_hidden: bool = False) -> dict[str, Any]:
    return {"items": get_service(request).list_allocations(show_hidden=show_hidden)}


@router.get("/transactions")
def transactions(
    request: Request,
    *,
    limit: int = Query(default=500, ge=1, le=10_000),
    offset: int = Query(default=0, ge=0),
    show_hidden: bool = False,
    sort_by: str = Query(
        default="entry_order", pattern=r"^(date|amount_minor|status|created_at|entry_order)$"
    ),
    sort_dir: str = Query(default="asc", pattern=r"^(asc|desc)$"),
    account_id: str | None = None,
    category_id: str | None = None,
    status: str | None = Query(default=None, pattern=r"^(PENDING|CLEARED)$"),
    date_from: str | None = None,
    date_to: str | None = None,
    amount_min_minor: int | None = Query(default=None, ge=0),
    amount_max_minor: int | None = Query(default=None, ge=0),
) -> dict[str, Any]:
    return get_service(request).list_transactions(
        limit=limit,
        offset=offset,
        show_hidden=show_hidden,
        sort_by=sort_by,
        sort_dir=sort_dir,
        account_id=account_id,
        category_id=category_id,
        status=status,
        date_from=date_from,
        date_to=date_to,
        amount_min_minor=amount_min_minor,
        amount_max_minor=amount_max_minor,
    )


@router.post("/transactions")
def create_transaction(request: Request, payload: TransactionPayload) -> dict[str, Any]:
    try:
        return get_service(request).create_transaction(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/transactions/{transaction_id}")
def update_transaction(
    request: Request, transaction_id: str, payload: TransactionPayload
) -> dict[str, Any]:
    try:
        return get_service(request).update_transaction(transaction_id, payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/transactions/{transaction_id}")
def delete_transaction(request: Request, transaction_id: str) -> dict[str, Any]:
    get_service(request).delete_transaction(transaction_id)
    return {"ok": True}


@router.post("/transactions/{transaction_id}/restore")
def restore_transaction(request: Request, transaction_id: str) -> dict[str, Any]:
    try:
        return get_service(request).restore_transaction(transaction_id)
    except ValueError as exc:
        detail = str(exc)
        if "not found" in detail.lower():
            raise HTTPException(status_code=404, detail=detail) from exc
        if "already active" in detail.lower():
            raise HTTPException(status_code=400, detail=detail) from exc
        raise HTTPException(status_code=400, detail=detail) from exc


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
def accounts(request: Request, *, show_hidden: bool = False) -> dict[str, Any]:
    return {"items": get_service(request).list_accounts(show_hidden=show_hidden)}


@router.post("/accounts")
def create_account(request: Request, payload: AccountPayload) -> dict[str, Any]:
    return get_service(request).create_account(payload.model_dump())


@router.put("/accounts/{account_id}")
def update_account(
    request: Request, account_id: str, payload: AccountUpdatePayload
) -> dict[str, Any]:
    return get_service(request).update_account(account_id, payload.model_dump(exclude_none=True))


@router.get("/accounts/{account_id}/transactions/summary")
def account_transaction_summary(
    request: Request,
    account_id: str,
    *,
    days: int = Query(default=30, ge=1, le=365),
    show_hidden: bool = False,
) -> dict[str, Any]:
    return get_service(request).account_transaction_summary(
        account_id=account_id, days=days, show_hidden=show_hidden
    )


@router.get("/accounts/{account_id}/balance-trend")
def account_balance_trend(
    request: Request,
    account_id: str,
    *,
    period: str = Query(default="1m", pattern=r"^(7d|1m|3m|6m|1y|all)$"),
    show_hidden: bool = False,
) -> dict[str, Any]:
    return get_service(request).account_balance_trend(
        account_id=account_id, period=period, show_hidden=show_hidden
    )


@router.get("/assets-liabilities")
def assets_liabilities(request: Request) -> dict[str, Any]:
    return get_service(request).get_assets_liabilities()


@router.post("/accounts/{account_id}/positions")
def create_position(
    request: Request, account_id: str, payload: "InvestmentPositionPayload"
) -> dict[str, Any]:
    return get_service(request).create_investment_position(account_id, payload.model_dump())


@router.get("/accounts/{account_id}/positions")
def list_positions(request: Request, account_id: str) -> dict[str, Any]:
    return {"items": get_service(request).list_investment_positions(account_id)}


@router.post("/accounts/{account_id}/investment-statements")
def reconcile_investment_statement(
    request: Request, account_id: str, payload: InvestmentStatementPayload
) -> dict[str, Any]:
    return get_service(request).reconcile_investment_statement(account_id, payload.model_dump())


@router.get("/accounts/{account_id}/investment-statements/latest")
def latest_investment_statement(request: Request, account_id: str) -> dict[str, Any]:
    return get_service(request).latest_investment_statement(account_id)


@router.post("/accounts/{account_id}/reconciliations/draft")
def create_reconciliation_draft(
    request: Request, account_id: str, payload: ReconciliationDraftPayload
) -> dict[str, Any]:
    try:
        return get_service(request).create_reconciliation_draft(account_id, payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/reconciliations/{reconciliation_id}")
def get_reconciliation(request: Request, reconciliation_id: str) -> dict[str, Any]:
    try:
        return get_service(request).get_reconciliation(reconciliation_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/reconciliations/{reconciliation_id}/apply")
def apply_reconciliation(
    request: Request, reconciliation_id: str, payload: ReconciliationApplyPayload
) -> dict[str, Any]:
    try:
        return get_service(request).apply_reconciliation(reconciliation_id, payload.model_dump())
    except CommandConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        status = 409 if "stale" in str(exc).lower() else 400
        raise HTTPException(status_code=status, detail=str(exc)) from exc


@router.get("/accounts/{account_id}/reconciliations")
def list_reconciliations(request: Request, account_id: str) -> dict[str, Any]:
    return {"items": get_service(request).list_reconciliations(account_id)}


@router.get("/accounts/{account_id}/reconciliation-working-set")
def reconciliation_working_set(request: Request, account_id: str) -> dict[str, Any]:
    return get_service(request).reconciliation_working_set(account_id)


@router.get("/accounts/{account_id}/budget-links")
def account_budget_links(request: Request, account_id: str) -> dict[str, Any]:
    return {"items": get_service(request).list_account_budget_links(account_id)}


@router.put("/accounts/{account_id}/budget-links")
def set_account_budget_link(
    request: Request, account_id: str, payload: AccountBudgetLinkPayload
) -> dict[str, Any]:
    return get_service(request).set_account_budget_link(account_id, payload.model_dump())


@router.post("/accounts/{account_id}/investment-transfers")
def create_investment_transfer(
    request: Request, account_id: str, payload: InvestmentTransferPayload
) -> dict[str, Any]:
    try:
        return get_service(request).create_investment_transfer(account_id, payload.model_dump())
    except CommandConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/accounts/{account_id}/credit-card-payments")
def create_credit_card_payment(
    request: Request, account_id: str, payload: CreditCardPaymentPayload
) -> dict[str, Any]:
    try:
        return get_service(request).create_credit_card_payment(account_id, payload.model_dump())
    except CommandConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/accounts/{account_id}/cash-snapshots")
def create_cash_snapshot(
    request: Request, account_id: str, payload: "InvestmentCashSnapshotPayload"
) -> dict[str, Any]:
    return get_service(request).create_investment_cash_snapshot(account_id, payload.model_dump())


@router.get("/accounts/{account_id}/cash-snapshots")
def list_cash_snapshots(request: Request, account_id: str) -> dict[str, Any]:
    return {"items": get_service(request).list_investment_cash_snapshots(account_id)}


@router.post("/price-snapshots")
def create_price_snapshot(
    request: Request, payload: "InvestmentPriceSnapshotPayload"
) -> dict[str, Any]:
    return get_service(request).create_investment_price_snapshot(payload.model_dump())


@router.get("/tickers/{ticker}/price-snapshots")
def list_price_snapshots(request: Request, ticker: str) -> dict[str, Any]:
    return {"items": get_service(request).list_investment_price_snapshots(ticker)}


@router.post("/accounts/{account_id}/tracking-snapshots")
def create_tracking_snapshot(
    request: Request, account_id: str, payload: TrackingAccountSnapshotPayload
) -> dict[str, Any]:
    return get_service(request).create_tracking_snapshot(account_id, payload.model_dump())


@router.post("/accounts/{account_id}/cutovers")
def create_tracking_cutover(
    request: Request, account_id: str, payload: TrackingCutoverPayload
) -> dict[str, Any]:
    try:
        return get_service(request).create_tracking_cutover(
            account_id, payload.model_dump(mode="json")
        )
    except CommandConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/accounts/{account_id}/tracking-snapshots")
def list_tracking_snapshots(request: Request, account_id: str) -> dict[str, Any]:
    return {"items": get_service(request).list_tracking_snapshots(account_id)}


@router.post("/accounts/{account_id}/loan-snapshots")
def create_loan_snapshot(
    request: Request, account_id: str, payload: LoanBalanceSnapshotPayload
) -> dict[str, Any]:
    return get_service(request).create_loan_snapshot(account_id, payload.model_dump())


@router.get("/accounts/{account_id}/loan-snapshots")
def list_loan_snapshots(request: Request, account_id: str) -> dict[str, Any]:
    return {"items": get_service(request).list_loan_snapshots(account_id)}


@router.get("/accounts/{account_id}/loan-projection")
def loan_projection(request: Request, account_id: str) -> dict[str, object]:
    return get_service(request).get_loan_projection(account_id)


@router.post("/accounts/{account_id}/loan-payments")
def create_loan_payment(
    request: Request, account_id: str, payload: LoanPaymentPayload
) -> dict[str, Any]:
    return get_service(request).create_loan_payment(account_id, payload.model_dump())


@router.get("/accounts/{account_id}/loan-payments")
def list_loan_payments(request: Request, account_id: str) -> dict[str, Any]:
    return {"items": get_service(request).list_loan_payments(account_id)}


@router.post("/accounts/{account_id}/tangible-valuations")
def create_tangible_valuation(
    request: Request, account_id: str, payload: TangibleAssetValuationPayload
) -> dict[str, Any]:
    return get_service(request).create_tangible_asset_valuation(account_id, payload.model_dump())


@router.get("/accounts/{account_id}/tangible-valuations")
def list_tangible_valuations(request: Request, account_id: str) -> dict[str, Any]:
    return {"items": get_service(request).list_tangible_asset_valuations(account_id)}


@router.get("/categories")
def categories(
    request: Request, *, month: str | None = None, show_hidden: bool = False
) -> dict[str, Any]:
    service = get_service(request)
    active_month = month or service.default_budget_month()
    items = service.list_categories(month=active_month, show_hidden=show_hidden)
    return {
        "groups": service.list_category_groups(
            month=active_month,
            show_hidden=show_hidden,
            precomputed_categories=items,
        ),
        "items": items,
    }


@router.get("/category-activity")
def category_activity(request: Request) -> dict[str, Any]:
    return {"items": get_service(request).list_category_activity()}


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


@router.get("/categories/{category_id}/goal")
def get_category_goal(request: Request, category_id: str) -> dict[str, Any]:
    return get_service(request).get_category_goal(category_id)


@router.put("/categories/{category_id}/goal")
def update_category_goal(
    request: Request, category_id: str, payload: GoalPayload
) -> dict[str, Any]:
    return get_service(request).update_category_goal(
        category_id, payload.model_dump(exclude_none=True)
    )


@router.get("/net-worth")
def net_worth(request: Request) -> dict[str, Any]:
    return get_service(request).get_net_worth()
