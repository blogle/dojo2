from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime
from uuid import NAMESPACE_URL, uuid5

from duckdb import DuckDBPyConnection

from dojo.constants import (
    ACCOUNT_CLASS_INVESTMENT,
    ACCOUNT_CLASS_LOAN,
    ACCOUNT_CLASS_TANGIBLE_ASSET,
    ACCOUNT_CLASS_TRACKING,
    DERIVATION_METHOD_TRANSFER_IN_ONLY,
    LINK_BEHAVIOR_INVESTMENT_CONTRIBUTION,
    LINK_BEHAVIOR_LOAN_PAYMENT,
    MAX_TS,
)
from dojo.scd import insert_version


def add_development_accounts(connection: DuckDBPyConnection, now: datetime) -> None:
    tracking_id = _id("account", "Harbor Education Fund")
    investment_id = _id("account", "Pinecone Brokerage")
    loan_id = _id("account", "Cedar Auto Loan")
    home_id = _id("account", "Juniper Home")

    _account(connection, tracking_id, "Harbor Education Fund", ACCOUNT_CLASS_TRACKING, now)
    _account(connection, investment_id, "Pinecone Brokerage", ACCOUNT_CLASS_INVESTMENT, now)
    _account(connection, loan_id, "Cedar Auto Loan", ACCOUNT_CLASS_LOAN, now)
    _account(connection, home_id, "Juniper Home", ACCOUNT_CLASS_TANGIBLE_ASSET, now)

    insert_version(
        connection,
        "tracking_account_details",
        _version("tracking-details", "Harbor Education Fund", now)
        | {
            "account_id": tracking_id,
            "polarity": "ASSET",
            "source": "Monthly estimate",
            "apy_minor": None,
        },
    )
    insert_version(
        connection,
        "investment_account_details",
        _version("investment-details", "Pinecone Brokerage", now)
        | {"account_id": investment_id, "self_managed": True, "tax_treatment": "TAXABLE_BROKERAGE"},
    )
    insert_version(
        connection,
        "loan_details",
        _version("loan-details", "Cedar Auto Loan", now)
        | {
            "account_id": loan_id,
            "original_amount_minor": 2_400_000,
            "origination_date": date(2024, 5, 1),
            "rate_minor": 625,
            "rate_type": "FIXED",
            "scheduled_principal_interest_minor": 31_500,
            "payment_frequency": "MONTHLY",
            "next_payment_date": date(2026, 10, 15),
            "maturity_date": date(2031, 5, 1),
            "remaining_term_months": 58,
            "recurring_extra_principal_minor": 0,
            "status": "IN_REPAYMENT",
        },
    )

    _link_category(
        connection, investment_id, "Emergency Reserve", LINK_BEHAVIOR_INVESTMENT_CONTRIBUTION, now
    )
    _link_category(connection, loan_id, "Auto Loan Payment", LINK_BEHAVIOR_LOAN_PAYMENT, now)

    instrument_id = _id("instrument", "PINECONE-CASH")
    connection.execute(
        """INSERT INTO investment_instruments
           (instrument_id, symbol, name, is_cash_equivalent, created_at, created_by_user_id)
           VALUES (?, ?, ?, TRUE, ?, NULL)""",
        (instrument_id, "CASH", "Brokerage cash", now),
    )
    connection.execute(
        """INSERT INTO investment_instruments
           (instrument_id, symbol, name, is_cash_equivalent, created_at, created_by_user_id)
           VALUES (?, ?, ?, FALSE, ?, NULL)""",
        (_id("instrument", "PINECONE-INDEX"), "IDX", "Broad market index", now),
    )

    for month in range(1, 10):
        effective_date = date(2026, month, monthrange(2026, month)[1])
        _snapshot(
            connection,
            "net_worth_valuations",
            "Harbor Education Fund",
            now,
            {
                "valuation_id": _id("tracking-valuation", str(month)),
                "account_id": tracking_id,
                "raw_name": "Harbor Education Fund",
                "effective_date": effective_date,
                "amount_minor": 2_100_000 + month * 46_000,
                "notes": "Fictional monthly statement",
                "metadata": None,
            },
        )
        _snapshot(
            connection,
            "tangible_asset_valuations",
            "Juniper Home",
            now,
            {
                "valuation_id": _id("home-valuation", str(month)),
                "account_id": home_id,
                "effective_date": effective_date,
                "amount_minor": 38_500_000 + month * 80_000,
                "source": "Independent estimate",
                "notes": "Fictional monthly estimate",
            },
        )
        _snapshot(
            connection,
            "investment_cash_snapshots",
            "Pinecone Brokerage",
            now,
            {
                "snapshot_id": _id("investment-cash-snapshot", str(month)),
                "account_id": investment_id,
                "effective_date": effective_date,
                "cash_balance_minor": 420_000 + month * 32_000,
                "record_order": month,
                "notes": "Monthly cash-only statement",
            },
        )
        _snapshot(
            connection,
            "loan_balance_snapshots",
            "Cedar Auto Loan",
            now,
            {
                "snapshot_id": _id("loan-snapshot", str(month)),
                "account_id": loan_id,
                "effective_date": effective_date,
                "principal_balance_minor": 1_840_000 - month * 24_000,
                "accrued_interest_minor": 1_800,
                "escrow_balance_minor": 0,
                "unapplied_credit_minor": None,
                "ytd_principal_paid_minor": month * 24_000,
                "ytd_interest_paid_minor": month * 7_500,
                "attributed_payment_minor": 31_500,
                "principal_reduction_minor": 24_000,
                "unknown_nonprincipal_minor": 0,
                "notes": "Fictional monthly lender statement",
            },
        )


def _account(
    connection: DuckDBPyConnection,
    account_id: str,
    name: str,
    account_class: str,
    now: datetime,
) -> None:
    insert_version(
        connection,
        "accounts",
        _version("account-row", name, now)
        | {
            "account_id": account_id,
            "account_class": account_class,
            "name": name,
            "institution": "Fictional Cooperative",
            "account_number_last4": None,
            "is_hidden": False,
            "is_active": True,
            "metadata": "{}",
        },
    )


def _link_category(
    connection: DuckDBPyConnection,
    account_id: str,
    category_name: str,
    behavior: str,
    now: datetime,
) -> None:
    category = connection.execute(
        "SELECT category_id FROM current_categories WHERE name = ?", (category_name,)
    ).fetchone()
    if category is None:
        raise RuntimeError(f"Development fixture category is missing: {category_name}")
    link_name = f"{account_id}:{category_name}"
    insert_version(
        connection,
        "account_budget_links",
        _version("account-budget-link", link_name, now)
        | {
            "account_id": account_id,
            "category_id": category[0],
            "link_behavior": behavior,
            "derivation_method": DERIVATION_METHOD_TRANSFER_IN_ONLY,
            "effective_date": date(2026, 1, 1),
        },
    )


def _snapshot(
    connection: DuckDBPyConnection,
    table: str,
    identity: str,
    now: datetime,
    payload: dict[str, object],
) -> None:
    insert_version(
        connection,
        table,
        _version(f"{table}-row", f"{identity}:{payload['effective_date']}", now) | payload,
    )


def _version(kind: str, key: str, now: datetime) -> dict[str, object]:
    return {
        "row_id": _id(kind, key),
        "valid_from": now,
        "valid_to": MAX_TS,
        "created_at": now,
        "created_by_user_id": None,
    }


def _id(kind: str, key: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"dojo:development-fixture:{kind}:{key}"))
