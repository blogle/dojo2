from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from typing import Any

from dojo.constants import (
    ACCOUNT_CLASS_BUDGET,
    CATEGORY_KIND_CREDIT_CARD_PAYMENT,
    CATEGORY_KIND_STANDARD,
    STATUS_CLEARED,
    SYSTEM_CATEGORY_ATB,
    SYSTEM_CATEGORY_BALANCE_ADJUSTMENT,
    SYSTEM_CATEGORY_STARTING_BALANCE,
    SYSTEM_CATEGORY_TRANSFER,
)
from dojo.importer import ParsedImportBundle
from dojo.sql import load_sql

ACCOUNT_RANGE_REFS = [
    "trx_Dates",
    "trx_Outflows",
    "trx_Inflows",
    "trx_Accounts",
    "trx_Statuses",
]
CATEGORY_RANGE_REFS = [
    "r_ConfigurationData",
    "UserDefCategories",
    "HiddenCategories",
    "trx_Categories",
    "cts_FromCategories",
    "cts_ToCategories",
]
ALLOCATION_RANGE_REFS = [
    "cts_Dates",
    "cts_Amounts",
    "cts_FromCategories",
    "cts_ToCategories",
]
NET_WORTH_RANGE_REFS = ["ntw_Dates", "ntw_Amounts", "ntw_Categories", "NetWorthDebts"]


@dataclass(slots=True)
class SourceCategorySnapshot:
    group_name: str
    category_kind: str
    is_hidden: bool
    linked_account_name: str | None
    available_minor: int
    month_activity_minor: dict[str, int]
    month_budgeted_minor: dict[str, int]
    starting_available_minor: dict[str, int]


def build_validation_report(service: Any, bundle: ParsedImportBundle) -> dict[str, Any]:
    months = _collect_months(bundle)
    current_month = service.default_budget_month()
    if current_month not in months:
        months.append(current_month)
        months.sort()

    expected_accounts = _expected_account_balances(bundle)
    expected_categories = _expected_category_snapshots(bundle, months)
    expected_atb = _expected_available_to_budget(bundle)
    expected_group_totals = _expected_group_totals(bundle, expected_categories, months)
    expected_budget_summaries = _expected_budget_summaries(
        bundle, expected_categories, expected_atb, months, show_hidden=False
    )
    expected_budget_summaries_hidden = _expected_budget_summaries(
        bundle, expected_categories, expected_atb, months, show_hidden=True
    )
    expected_net_worth = _expected_net_worth(bundle, expected_accounts)

    checks: list[dict[str, Any]] = []

    actual_accounts_all = {row["name"]: row for row in service.list_accounts(show_hidden=True)}
    actual_accounts_visible = {row["name"]: row for row in service.list_accounts(show_hidden=False)}
    actual_atb = service.compute_available_to_budget()
    actual_categories = _actual_category_snapshots(service, months)
    actual_group_names = [
        row["name"]
        for row in service.db.fetch_all(load_sql("queries/current_category_groups_ordered"))
    ]
    actual_group_totals = _category_group_totals(actual_group_names, actual_categories, months)
    actual_budget_summaries = _actual_budget_summaries(
        service, actual_categories, actual_atb, months, show_hidden=False
    )
    actual_budget_summaries_hidden = _actual_budget_summaries(
        service, actual_categories, actual_atb, months, show_hidden=True
    )
    actual_net_worth = service.get_net_worth()

    for account in bundle.accounts:
        expected = expected_accounts[account.name]
        actual = actual_accounts_all[account.name]
        for field, notes in (
            ("actual", "Signed transaction sum across all statuses."),
            ("pending", "Signed transaction sum for pending rows only."),
            ("cleared", "Signed transaction sum for cleared rows only."),
            (
                "display",
                "UI display balance; credit-card liabilities are displayed as positive when configured.",
            ),
        ):
            _append_money_check(
                checks,
                label=f"account.{field}",
                entity_type="account",
                entity_name=account.name,
                expected_minor=expected[field],
                actual_minor=actual[f"{field}_balance_minor"]
                if field != "display"
                else actual["display_balance_minor"],
                source_reference=ACCOUNT_RANGE_REFS,
                notes=notes,
            )

        _append_value_check(
            checks,
            label="account.hidden",
            entity_type="account",
            entity_name=account.name,
            expected_value=account.is_hidden,
            actual_value=actual["is_hidden"],
            source_reference=["HiddenAccounts", "cfg_Accounts", "cfg_Cards"],
            notes="Hidden account metadata must survive import and API serialization.",
        )
        _append_value_check(
            checks,
            label="account.visible_list_membership",
            entity_type="account",
            entity_name=account.name,
            expected_value=not account.is_hidden,
            actual_value=account.name in actual_accounts_visible,
            source_reference=["HiddenAccounts"],
            notes="Hidden accounts should be excluded from the default accounts list.",
        )

    for month in months:
        for category in bundle.categories:
            expected_category = expected_categories[category.name]
            actual_category = actual_categories[category.name]
            for field, notes in (
                (
                    "available_minor",
                    "Carryforward plus budgeted movement plus categorized activity according to dojo MVP semantics.",
                ),
                (
                    "month_activity_minor",
                    "Current-month categorized activity for the category.",
                ),
                (
                    "month_budgeted_minor",
                    "Current-month allocation movement into and out of the category bucket.",
                ),
                (
                    "starting_available_minor",
                    "Starting available balance for the selected month before current-month budgeted movement and activity.",
                ),
            ):
                expected_minor = (
                    getattr(expected_category, field)[month]
                    if isinstance(getattr(expected_category, field), dict)
                    else getattr(expected_category, field)
                )
                actual_minor = (
                    getattr(actual_category, field)[month]
                    if isinstance(getattr(actual_category, field), dict)
                    else getattr(actual_category, field)
                )
                _append_money_check(
                    checks,
                    label=f"category.{field.removesuffix('_minor')}",
                    entity_type="category",
                    entity_name=category.name,
                    month=month,
                    expected_minor=expected_minor,
                    actual_minor=actual_minor,
                    source_reference=CATEGORY_RANGE_REFS + ALLOCATION_RANGE_REFS,
                    notes=notes,
                )

            _append_value_check(
                checks,
                label="category.hidden",
                entity_type="category",
                entity_name=category.name,
                expected_value=category.is_hidden,
                actual_value=actual_category.is_hidden,
                month=month,
                source_reference=["HiddenCategories", "r_ConfigurationData"],
                notes="Hidden category metadata must survive import and API serialization.",
            )
            _append_value_check(
                checks,
                label="category.visible_budget_membership",
                entity_type="category",
                entity_name=category.name,
                expected_value=not category.is_hidden,
                actual_value=not actual_category.is_hidden,
                month=month,
                source_reference=["HiddenCategories", "r_ConfigurationData"],
                notes="Hidden categories should be excluded from the default budget/category lists.",
            )

        for group_name, totals in expected_group_totals[month].items():
            actual_group = actual_group_totals[month][group_name]
            for field, note in (
                (
                    "available",
                    "Hidden-inclusive group available total derived from all imported categories in the group.",
                ),
                (
                    "month_activity",
                    "Hidden-inclusive group month activity total derived from all imported categories in the group.",
                ),
                (
                    "month_budgeted",
                    "Hidden-inclusive group month budgeted total derived from all imported categories in the group.",
                ),
                (
                    "starting_available",
                    "Hidden-inclusive group starting-available total derived from all imported categories in the group.",
                ),
            ):
                _append_money_check(
                    checks,
                    label=f"group.{field}_total_with_hidden",
                    entity_type="category_group",
                    entity_name=group_name,
                    month=month,
                    expected_minor=totals[f"{field}_with_hidden_minor"],
                    actual_minor=actual_group[f"{field}_with_hidden_minor"],
                    source_reference=CATEGORY_RANGE_REFS + ALLOCATION_RANGE_REFS,
                    notes=note,
                )
            for field, note in (
                (
                    "available",
                    "Visible group available total derived from visible categories in the group.",
                ),
                (
                    "month_activity",
                    "Visible group month activity total derived from visible categories in the group.",
                ),
                (
                    "month_budgeted",
                    "Visible group month budgeted total derived from visible categories in the group.",
                ),
                (
                    "starting_available",
                    "Visible group starting-available total derived from visible categories in the group.",
                ),
            ):
                _append_money_check(
                    checks,
                    label=f"group.{field}_total",
                    entity_type="category_group",
                    entity_name=group_name,
                    month=month,
                    expected_minor=totals[f"{field}_minor"],
                    actual_minor=actual_group[f"{field}_minor"],
                    source_reference=CATEGORY_RANGE_REFS + ALLOCATION_RANGE_REFS,
                    notes=note,
                )

        _append_money_check(
            checks,
            label="budget.available_to_budget",
            entity_type="budget_month",
            entity_name=month,
            month=month,
            expected_minor=expected_atb,
            actual_minor=actual_atb,
            source_reference=ACCOUNT_RANGE_REFS
            + ALLOCATION_RANGE_REFS
            + [
                "Dashboard!J3",
                "Calculations!B59",
                "v_AtoB",
                "v_StartingBalance",
                "v_BalanceAdjustment",
            ],
            notes="Imported and derived unallocated money available to assign to categories. Aspire renders this on Dashboard!J3 from Calculations!B59.",
        )
        for field in (
            "month_activity_minor",
            "month_budgeted_minor",
            "starting_available_minor",
            "reportable_income_minor",
            "spent_minor",
        ):
            _append_money_check(
                checks,
                label=f"budget.summary.{field.removesuffix('_minor')}",
                entity_type="budget_month",
                entity_name=month,
                month=month,
                expected_minor=expected_budget_summaries[month][field],
                actual_minor=actual_budget_summaries[month][field],
                source_reference=CATEGORY_RANGE_REFS + ALLOCATION_RANGE_REFS + ACCOUNT_RANGE_REFS,
                notes="Budget-page visible summary total for the selected month.",
            )
            _append_money_check(
                checks,
                label=f"budget.summary_with_hidden.{field.removesuffix('_minor')}",
                entity_type="budget_month",
                entity_name=month,
                month=month,
                expected_minor=expected_budget_summaries_hidden[month][field],
                actual_minor=actual_budget_summaries_hidden[month][field],
                source_reference=CATEGORY_RANGE_REFS + ALLOCATION_RANGE_REFS + ACCOUNT_RANGE_REFS,
                notes="Budget-page hidden-inclusive summary total for the selected month.",
            )

    visible_expected_total = sum(
        values["actual"]
        for name, values in expected_accounts.items()
        if not _account_hidden(bundle, name)
    )
    visible_actual_total = sum(
        account["actual_balance_minor"] for account in actual_accounts_visible.values()
    )
    _append_money_check(
        checks,
        label="accounts.visible_total",
        entity_type="account_collection",
        entity_name="visible_accounts",
        expected_minor=visible_expected_total,
        actual_minor=visible_actual_total,
        source_reference=ACCOUNT_RANGE_REFS + ["HiddenAccounts"],
        notes="Visible accounts page total should exclude hidden accounts.",
    )

    _append_money_check(
        checks,
        label="net_worth.total",
        entity_type="net_worth",
        entity_name="current",
        expected_minor=expected_net_worth["current_net_worth_minor"],
        actual_minor=actual_net_worth["current_net_worth_minor"],
        source_reference=ACCOUNT_RANGE_REFS + NET_WORTH_RANGE_REFS,
        notes="Budget-account values come from ledger balances; non-budget tracking values come from the latest imported valuation rows.",
    )
    _append_value_check(
        checks,
        label="net_worth.ledger_labels_present",
        entity_type="net_worth",
        entity_name="ledger_rows",
        expected_value=len(expected_net_worth["ledger_budget_accounts"]),
        actual_value=sum(
            1
            for item in actual_net_worth["items"]
            if item.get("source") == "ledger" and item.get("account_name")
        ),
        source_reference=["/api/net-worth"],
        notes="Every ledger-derived net-worth row must include a visible account label.",
    )

    actual_net_worth_items = defaultdict(list)
    for item in actual_net_worth["items"]:
        actual_net_worth_items[item.get("account_name") or item.get("name")].append(item)

    for account_name, expected_minor in expected_net_worth["ledger_budget_accounts"].items():
        item = next(
            row for row in actual_net_worth_items[account_name] if row.get("source") == "ledger"
        )
        _append_money_check(
            checks,
            label="net_worth.ledger_budget_account",
            entity_type="account",
            entity_name=account_name,
            expected_minor=expected_minor,
            actual_minor=item["net_worth_minor"],
            source_reference=ACCOUNT_RANGE_REFS,
            notes="Budget-account net worth must be derived from imported budget-account balances, not duplicated net-worth rows.",
        )

    for account_name, expected_minor in expected_net_worth["tracking_latest_values"].items():
        item = next(
            row
            for row in actual_net_worth_items[account_name]
            if row.get("source") == "imported_valuation" and not row.get("ignored_import_value")
        )
        _append_money_check(
            checks,
            label="net_worth.imported_tracking_value",
            entity_type="account",
            entity_name=account_name,
            expected_minor=expected_minor,
            actual_minor=item["net_worth_minor"],
            source_reference=NET_WORTH_RANGE_REFS,
            notes="Tracking account net worth should use the latest imported valuation for the account.",
        )

    for account_name, expected_minor in expected_net_worth["ignored_budget_valuations"].items():
        item = next(
            row
            for row in actual_net_worth_items[account_name]
            if row.get("source") == "imported_valuation" and row.get("ignored_import_value")
        )
        _append_money_check(
            checks,
            label="net_worth.ignored_budget_import_value",
            entity_type="account",
            entity_name=account_name,
            expected_minor=expected_minor,
            actual_minor=item["net_worth_minor"],
            source_reference=NET_WORTH_RANGE_REFS,
            notes="This duplicated Aspire valuation is expected to be preserved for diagnostics and ignored in the native total.",
        )
        _append_value_check(
            checks,
            label="net_worth.ignored_budget_import_flag",
            entity_type="account",
            entity_name=account_name,
            expected_value=True,
            actual_value=item["ignored_import_value"],
            source_reference=NET_WORTH_RANGE_REFS,
            notes="Duplicated budget-account imported net-worth rows must be flagged as ignored.",
        )

    _append_value_check(
        checks,
        label="net_worth.ambiguous_duplicate_count",
        entity_type="net_worth",
        entity_name="ambiguous_duplicates",
        expected_value=0,
        actual_value=len(expected_net_worth["ambiguous_duplicates"]),
        source_reference=NET_WORTH_RANGE_REFS,
        notes="Ambiguous normalized matches between budget accounts and net-worth snapshot categories must be surfaced as validation failures instead of silently double-counted.",
    )

    hard_failures = [check for check in checks if not check["passed"]]
    return {
        "passed": not hard_failures,
        "checks": checks,
        "hard_failures": hard_failures,
        "warnings": [],
        "summary": {
            "source_kind": bundle.source_kind,
            "spreadsheet_id": bundle.spreadsheet_id,
            "spreadsheet_title": bundle.spreadsheet_title,
            "current_month": current_month,
            "months_validated": months,
            "account_count": len(bundle.accounts),
            "category_count": len(bundle.categories),
            "group_count": len(bundle.groups),
            "transaction_count": len(bundle.transactions),
            "allocation_count": len(bundle.allocations),
            "valuation_count": len(bundle.valuations),
            "check_count": len(checks),
            "failed_check_count": len(hard_failures),
        },
    }


def _collect_months(bundle: ParsedImportBundle) -> list[str]:
    months = {row.date.strftime("%Y-%m") for row in bundle.transactions}
    months.update(row.date.strftime("%Y-%m") for row in bundle.allocations)
    return sorted(months)


def _actual_category_snapshots(
    service: Any, months: list[str]
) -> dict[str, SourceCategorySnapshot]:
    categories = service.db.fetch_all(load_sql("queries/current_categories_ordered"))
    groups = {
        row["group_id"]: row
        for row in service.db.fetch_all(load_sql("queries/current_category_groups_ordered"))
    }
    accounts = {
        row["account_id"]: row for row in service.db.fetch_all(load_sql("queries/current_accounts"))
    }
    settings = {
        row["linked_payment_category_id"]: row
        for row in service.db.fetch_all(load_sql("queries/current_budget_account_settings"))
        if row["linked_payment_category_id"] is not None
    }
    transactions = service.db.fetch_all(load_sql("queries/current_transactions"))
    allocations = service.db.fetch_all(load_sql("queries/current_allocations"))

    category_name_by_id = {row["category_id"]: row["name"] for row in categories}
    category_kind_by_id = {row["category_id"]: row["category_kind"] for row in categories}
    category_name_by_bucket_id = {
        service._bucket_id_for_category(row["category_id"]): row["name"] for row in categories
    }
    payment_category_by_account_name = {
        accounts[row["account_id"]]["name"]: category_name_by_id[category_id]
        for category_id, row in settings.items()
    }

    bucket_balances = {row["name"]: 0 for row in categories}
    credit_card_spend: dict[str, int] = defaultdict(int)
    allocations_by_month: dict[str, list[tuple[str, str, int]]] = defaultdict(list)
    for allocation in allocations:
        from_name = (
            "Available to budget"
            if allocation["from_bucket_id"]
            == service._bucket_id_from_name("Available to budget", {})
            else category_name_by_bucket_id[allocation["from_bucket_id"]]
        )
        to_name = (
            "Available to budget"
            if allocation["to_bucket_id"] == service._bucket_id_from_name("Available to budget", {})
            else category_name_by_bucket_id[allocation["to_bucket_id"]]
        )
        month = allocation["date"].strftime("%Y-%m")
        allocations_by_month[month].append((from_name, to_name, allocation["amount_minor"]))
        if to_name != "Available to budget":
            bucket_balances[to_name] += allocation["amount_minor"]
        if from_name != "Available to budget":
            bucket_balances[from_name] -= allocation["amount_minor"]

    activity_by_month: dict[str, dict[str, int]] = {
        row["name"]: defaultdict(int) for row in categories
    }
    for transaction in transactions:
        month = transaction["date"].strftime("%Y-%m")
        account_name = accounts[transaction["account_id"]]["name"]
        category_name = category_name_by_id.get(transaction["category_id"])
        if category_name is not None:
            activity_by_month[category_name][month] += transaction["amount_minor"]
            if category_kind_by_id[transaction["category_id"]] == CATEGORY_KIND_STANDARD:
                bucket_balances[category_name] += transaction["amount_minor"]
        payment_category_name = payment_category_by_account_name.get(account_name)
        if payment_category_name is not None and transaction["category_id"] is not None:
            credit_card_spend[payment_category_name] += -transaction["amount_minor"]
        if (
            payment_category_name is not None
            and transaction["system_category"] == SYSTEM_CATEGORY_TRANSFER
            and transaction["amount_minor"] > 0
        ):
            credit_card_spend[payment_category_name] -= transaction["amount_minor"]

    snapshots: dict[str, SourceCategorySnapshot] = {}
    for category in categories:
        category_name = category["name"]
        budgeted_by_month: dict[str, int] = {}
        starting_by_month: dict[str, int] = {}
        running_balance = 0
        allocation_balance = 0
        for month in months:
            starting_by_month[month] = running_balance
            month_budgeted = 0
            for from_name, to_name, amount_minor in allocations_by_month.get(month, []):
                if to_name == category_name:
                    month_budgeted += amount_minor
                if from_name == category_name:
                    month_budgeted -= amount_minor
            budgeted_by_month[month] = month_budgeted
            if category["category_kind"] == CATEGORY_KIND_STANDARD:
                running_balance += month_budgeted + activity_by_month[category_name].get(month, 0)
            else:
                starting_by_month[month] = allocation_balance
                allocation_balance += month_budgeted
        available_minor = bucket_balances[category_name]
        if category["category_kind"] == CATEGORY_KIND_CREDIT_CARD_PAYMENT:
            available_minor = allocation_balance + credit_card_spend[category_name]
        linked_account_name = None
        setting = settings.get(category["category_id"])
        if setting is not None:
            linked_account_name = accounts[setting["account_id"]]["name"]
        snapshots[category_name] = SourceCategorySnapshot(
            group_name=groups[category["group_id"]]["name"],
            category_kind=category["category_kind"],
            is_hidden=category["is_hidden"],
            linked_account_name=linked_account_name,
            available_minor=available_minor,
            month_activity_minor={
                month: activity_by_month[category_name].get(month, 0) for month in months
            },
            month_budgeted_minor=budgeted_by_month,
            starting_available_minor=starting_by_month,
        )
    return snapshots


def _category_group_totals(
    group_names: list[str],
    categories: dict[str, SourceCategorySnapshot],
    months: list[str],
) -> dict[str, dict[str, dict[str, int]]]:
    result: dict[str, dict[str, dict[str, int]]] = {}
    for month in months:
        month_totals: dict[str, dict[str, int]] = {}
        for group_name in group_names:
            visible_categories = [
                snapshot
                for snapshot in categories.values()
                if snapshot.group_name == group_name and not snapshot.is_hidden
            ]
            all_categories = [
                snapshot for snapshot in categories.values() if snapshot.group_name == group_name
            ]
            month_totals[group_name] = {
                "available_minor": sum(item.available_minor for item in visible_categories),
                "available_with_hidden_minor": sum(item.available_minor for item in all_categories),
                "month_activity_minor": sum(
                    item.month_activity_minor[month] for item in visible_categories
                ),
                "month_activity_with_hidden_minor": sum(
                    item.month_activity_minor[month] for item in all_categories
                ),
                "month_budgeted_minor": sum(
                    item.month_budgeted_minor[month] for item in visible_categories
                ),
                "month_budgeted_with_hidden_minor": sum(
                    item.month_budgeted_minor[month] for item in all_categories
                ),
                "starting_available_minor": sum(
                    item.starting_available_minor[month] for item in visible_categories
                ),
                "starting_available_with_hidden_minor": sum(
                    item.starting_available_minor[month] for item in all_categories
                ),
            }
        result[month] = month_totals
    return result


def _actual_budget_summaries(
    service: Any,
    categories: dict[str, SourceCategorySnapshot],
    atb_minor: int,
    months: list[str],
    *,
    show_hidden: bool,
) -> dict[str, dict[str, int]]:
    transactions = service.db.fetch_all(
        load_sql("queries/current_transactions_amount_date_category_system")
    )
    category_rows = {
        row["category_id"]: row
        for row in service.db.fetch_all(load_sql("queries/current_categories"))
    }
    summaries: dict[str, dict[str, int]] = {}
    for month in months:
        visible = [
            category
            for category in categories.values()
            if category.category_kind == CATEGORY_KIND_STANDARD
            and (show_hidden or not category.is_hidden)
        ]
        spent_minor = 0
        refunds_minor = 0
        reportable_income_minor = 0
        for transaction in transactions:
            if transaction["date"].strftime("%Y-%m") != month:
                continue
            if (
                transaction["system_category"] == SYSTEM_CATEGORY_ATB
                and transaction["amount_minor"] > 0
            ):
                reportable_income_minor += transaction["amount_minor"]
            if transaction["category_id"] is None:
                continue
            category_row = category_rows[transaction["category_id"]]
            if category_row["category_kind"] != CATEGORY_KIND_STANDARD:
                continue
            if category_row["is_hidden"] and not show_hidden:
                continue
            if transaction["amount_minor"] < 0:
                spent_minor += -transaction["amount_minor"]
            else:
                refunds_minor += transaction["amount_minor"]
        summaries[month] = {
            "month_activity_minor": sum(
                category.month_activity_minor[month] for category in visible
            ),
            "month_budgeted_minor": sum(
                category.month_budgeted_minor[month] for category in visible
            ),
            "starting_available_minor": sum(
                category.starting_available_minor[month] for category in visible
            ),
            "reportable_income_minor": reportable_income_minor,
            "spent_minor": spent_minor - refunds_minor,
            "available_to_budget_minor": atb_minor,
        }
    return summaries


def _expected_account_balances(bundle: ParsedImportBundle) -> dict[str, dict[str, int]]:
    account_meta = {account.name: account for account in bundle.accounts}
    balances = {
        account.name: {"actual": 0, "pending": 0, "cleared": 0, "display": 0}
        for account in bundle.accounts
        if account.account_class == ACCOUNT_CLASS_BUDGET
    }
    for transaction in bundle.transactions:
        balance = balances[transaction.account_name]
        balance["actual"] += transaction.amount_minor
        if transaction.status == STATUS_CLEARED:
            balance["cleared"] += transaction.amount_minor
        else:
            balance["pending"] += transaction.amount_minor
    for account_name, values in balances.items():
        display = values["actual"]
        if account_meta[account_name].display_liability_positive:
            display = -display
        values["display"] = display
    return balances


def _expected_available_to_budget(bundle: ParsedImportBundle) -> int:
    total = 0
    for transaction in bundle.transactions:
        if transaction.system_category == SYSTEM_CATEGORY_STARTING_BALANCE:
            if transaction.amount_minor > 0:
                total += transaction.amount_minor
            continue
        if transaction.system_category in {SYSTEM_CATEGORY_ATB, SYSTEM_CATEGORY_BALANCE_ADJUSTMENT}:
            total += transaction.amount_minor
    for allocation in bundle.allocations:
        if allocation.to_name == "Available to budget":
            total += allocation.amount_minor
        if allocation.from_name == "Available to budget":
            total -= allocation.amount_minor
    return total


def _expected_category_snapshots(
    bundle: ParsedImportBundle, months: list[str]
) -> dict[str, SourceCategorySnapshot]:
    categories = {category.name: category for category in bundle.categories}
    bucket_balances = {category.name: 0 for category in bundle.categories}
    credit_card_spend: dict[str, int] = defaultdict(int)

    allocations_by_month = defaultdict(list)
    for allocation in bundle.allocations:
        allocations_by_month[allocation.date.strftime("%Y-%m")].append(allocation)
        if allocation.to_name != "Available to budget":
            bucket_balances[allocation.to_name] += allocation.amount_minor
        if allocation.from_name != "Available to budget":
            bucket_balances[allocation.from_name] -= allocation.amount_minor

    activity_by_month: dict[str, dict[str, int]] = {
        category.name: defaultdict(int) for category in bundle.categories
    }
    for transaction in bundle.transactions:
        month = transaction.date.strftime("%Y-%m")
        if transaction.category_name is not None:
            activity_by_month[transaction.category_name][month] += transaction.amount_minor
            category = categories[transaction.category_name]
            if category.category_kind == CATEGORY_KIND_STANDARD:
                bucket_balances[transaction.category_name] += transaction.amount_minor
        for category in bundle.categories:
            if (
                category.category_kind == CATEGORY_KIND_CREDIT_CARD_PAYMENT
                and category.linked_account_name == transaction.account_name
                and transaction.category_name is not None
            ):
                credit_card_spend[category.name] += -transaction.amount_minor
        for category in bundle.categories:
            if (
                category.category_kind == CATEGORY_KIND_CREDIT_CARD_PAYMENT
                and category.linked_account_name == transaction.account_name
                and transaction.system_category == SYSTEM_CATEGORY_TRANSFER
                and transaction.amount_minor > 0
            ):
                credit_card_spend[category.name] -= transaction.amount_minor

    snapshots: dict[str, SourceCategorySnapshot] = {}
    for category in bundle.categories:
        budgeted_by_month = {}
        carried_by_month = {}
        running_balance = 0
        allocation_balance = 0
        for month in months:
            carried_by_month[month] = running_balance
            month_budgeted = 0
            for allocation in allocations_by_month.get(month, []):
                if allocation.to_name == category.name:
                    month_budgeted += allocation.amount_minor
                if allocation.from_name == category.name:
                    month_budgeted -= allocation.amount_minor
            budgeted_by_month[month] = month_budgeted
            if category.category_kind == CATEGORY_KIND_STANDARD:
                running_balance += month_budgeted + activity_by_month[category.name].get(month, 0)
            else:
                carried_by_month[month] = allocation_balance
                allocation_balance += month_budgeted
        available_minor = bucket_balances[category.name]
        if category.category_kind == CATEGORY_KIND_CREDIT_CARD_PAYMENT:
            available_minor = allocation_balance + credit_card_spend[category.name]
        snapshots[category.name] = SourceCategorySnapshot(
            group_name=category.group_name,
            category_kind=category.category_kind,
            is_hidden=category.is_hidden,
            linked_account_name=category.linked_account_name,
            available_minor=available_minor,
            month_activity_minor={
                month: activity_by_month[category.name].get(month, 0) for month in months
            },
            month_budgeted_minor=budgeted_by_month,
            starting_available_minor=carried_by_month,
        )
    return snapshots


def _expected_group_totals(
    bundle: ParsedImportBundle,
    categories: dict[str, SourceCategorySnapshot],
    months: list[str],
) -> dict[str, dict[str, dict[str, int]]]:
    result: dict[str, dict[str, dict[str, int]]] = {}
    group_names = [group.name for group in bundle.groups]
    for month in months:
        month_totals: dict[str, dict[str, int]] = {}
        for group_name in group_names:
            visible_categories = [
                snapshot
                for snapshot in categories.values()
                if snapshot.group_name == group_name and not snapshot.is_hidden
            ]
            all_categories = [
                snapshot for snapshot in categories.values() if snapshot.group_name == group_name
            ]
            month_totals[group_name] = {
                "available_minor": sum(item.available_minor for item in visible_categories),
                "available_with_hidden_minor": sum(item.available_minor for item in all_categories),
                "month_activity_minor": sum(
                    item.month_activity_minor[month] for item in visible_categories
                ),
                "month_activity_with_hidden_minor": sum(
                    item.month_activity_minor[month] for item in all_categories
                ),
                "month_budgeted_minor": sum(
                    item.month_budgeted_minor[month] for item in visible_categories
                ),
                "month_budgeted_with_hidden_minor": sum(
                    item.month_budgeted_minor[month] for item in all_categories
                ),
                "starting_available_minor": sum(
                    item.starting_available_minor[month] for item in visible_categories
                ),
                "starting_available_with_hidden_minor": sum(
                    item.starting_available_minor[month] for item in all_categories
                ),
            }
        result[month] = month_totals
    return result


def _expected_budget_summaries(
    bundle: ParsedImportBundle,
    categories: dict[str, SourceCategorySnapshot],
    atb_minor: int,
    months: list[str],
    *,
    show_hidden: bool,
) -> dict[str, dict[str, int]]:
    summaries: dict[str, dict[str, int]] = {}
    for month in months:
        visible = [
            category
            for category in categories.values()
            if category.category_kind == CATEGORY_KIND_STANDARD
            and (show_hidden or not category.is_hidden)
        ]
        spent_minor = 0
        refunds_minor = 0
        summaries[month] = {
            "month_activity_minor": sum(
                category.month_activity_minor[month] for category in visible
            ),
            "month_budgeted_minor": sum(
                category.month_budgeted_minor[month] for category in visible
            ),
            "starting_available_minor": sum(
                category.starting_available_minor[month] for category in visible
            ),
            "reportable_income_minor": sum(
                transaction.amount_minor
                for transaction in bundle.transactions
                if transaction.system_category == SYSTEM_CATEGORY_ATB
                and transaction.amount_minor > 0
                and transaction.date.strftime("%Y-%m") == month
            ),
            "spent_minor": 0,
            "available_to_budget_minor": atb_minor,
        }
        for category in visible:
            activity = category.month_activity_minor[month]
            if activity < 0:
                spent_minor += -activity
            else:
                refunds_minor += activity
        summaries[month]["spent_minor"] = spent_minor - refunds_minor
    return summaries


def _expected_net_worth(
    bundle: ParsedImportBundle, expected_accounts: dict[str, dict[str, int]]
) -> dict[str, Any]:
    latest_by_name: dict[str, tuple[date, int]] = {}
    ledger_budget_accounts = {
        account.name: expected_accounts[account.name]["actual"]
        for account in bundle.accounts
        if account.account_class == ACCOUNT_CLASS_BUDGET
    }
    ignored_budget_valuations: dict[str, int] = {}
    ambiguous_duplicates: dict[str, tuple[str, ...]] = {}
    for valuation in bundle.valuations:
        if valuation.match_kind == "AMBIGUOUS_BUDGET_ACCOUNT":
            ambiguous_duplicates[valuation.raw_name] = valuation.match_candidates
            continue
        if valuation.account_name in ledger_budget_accounts:
            ignored_budget_valuations[valuation.account_name] = valuation.amount_minor
            continue
        latest = latest_by_name.get(valuation.raw_name)
        if latest is None or valuation.effective_date >= latest[0]:
            latest_by_name[valuation.raw_name] = (valuation.effective_date, valuation.amount_minor)
    tracking_latest_values = {name: amount for name, (_dt, amount) in latest_by_name.items()}
    total = sum(ledger_budget_accounts.values()) + sum(tracking_latest_values.values())
    return {
        "current_net_worth_minor": total,
        "ledger_budget_accounts": ledger_budget_accounts,
        "tracking_latest_values": tracking_latest_values,
        "ignored_budget_valuations": ignored_budget_valuations,
        "ambiguous_duplicates": ambiguous_duplicates,
    }


def _account_hidden(bundle: ParsedImportBundle, account_name: str) -> bool:
    return next(account.is_hidden for account in bundle.accounts if account.name == account_name)


def _append_money_check(
    checks: list[dict[str, Any]],
    *,
    label: str,
    entity_type: str,
    entity_name: str,
    expected_minor: int,
    actual_minor: int,
    source_reference: list[str],
    notes: str,
    month: str | None = None,
) -> None:
    checks.append(
        {
            "label": label,
            "entity_type": entity_type,
            "entity_name": entity_name,
            "month": month,
            "expected_value": expected_minor,
            "actual_value": actual_minor,
            "expected_minor": expected_minor,
            "actual_minor": actual_minor,
            "absolute_delta_minor": abs(actual_minor - expected_minor),
            "passed": actual_minor == expected_minor,
            "source_reference": source_reference,
            "notes": notes,
        }
    )


def _append_value_check(
    checks: list[dict[str, Any]],
    *,
    label: str,
    entity_type: str,
    entity_name: str,
    expected_value: Any,
    actual_value: Any,
    source_reference: list[str],
    notes: str,
    month: str | None = None,
) -> None:
    checks.append(
        {
            "label": label,
            "entity_type": entity_type,
            "entity_name": entity_name,
            "month": month,
            "expected_value": expected_value,
            "actual_value": actual_value,
            "expected_minor": None,
            "actual_minor": None,
            "absolute_delta_minor": None,
            "passed": actual_value == expected_value,
            "source_reference": source_reference,
            "notes": notes,
        }
    )
