from __future__ import annotations

from datetime import date
from typing import Any
from uuid import NAMESPACE_URL, uuid4, uuid5

from dojo.constants import (
    ACCOUNT_CLASS_BUDGET,
    ACCOUNT_CLASS_TRACKING_BALANCE,
    BUDGET_ACCOUNT_TYPE_CREDIT_CARD,
    BUDGET_ACCOUNT_TYPE_DEPOSIT,
    CATEGORY_KIND_CREDIT_CARD_PAYMENT,
    CATEGORY_KIND_STANDARD,
    STATUS_CLEARED,
    STATUS_PENDING,
    SYSTEM_CATEGORY_ATB,
    SYSTEM_CATEGORY_STARTING_BALANCE,
)
from dojo.importer import (
    ParsedAccount,
    ParsedAllocation,
    ParsedCategory,
    ParsedGroup,
    ParsedImportBundle,
    ParsedTransaction,
    ParsedValuation,
)


class SyntheticDatasetConfig:
    def __init__(
        self,
        *,
        label: str,
        num_accounts: int = 5,
        num_categories: int = 10,
        num_months: int = 3,
        num_transactions: int = 1000,
        num_allocations_per_month: int = 20,
        num_net_worth_valuations: int = 5,
        seed: int = 42,
    ):
        self.label = label
        self.num_accounts = num_accounts
        self.num_categories = num_categories
        self.num_months = num_months
        self.num_transactions = num_transactions
        self.num_allocations_per_month = num_allocations_per_month
        self.num_net_worth_valuations = num_net_worth_valuations
        self.seed = seed


DATASET_SMALL = SyntheticDatasetConfig(
    label="1K",
    num_accounts=5,
    num_categories=10,
    num_months=3,
    num_transactions=1000,
    num_allocations_per_month=20,
)

DATASET_MEDIUM = SyntheticDatasetConfig(
    label="10K",
    num_accounts=10,
    num_categories=25,
    num_months=12,
    num_transactions=10_000,
    num_allocations_per_month=30,
)

DATASET_LARGE = SyntheticDatasetConfig(
    label="100K",
    num_accounts=20,
    num_categories=50,
    num_months=24,
    num_transactions=100_000,
    num_allocations_per_month=50,
)

DATASETS = [DATASET_SMALL, DATASET_MEDIUM, DATASET_LARGE]


def _seeded_rng(seed: int) -> Any:
    return __import__("random").Random(seed)


def _account_id(idx: int) -> str:
    return str(uuid5(NAMESPACE_URL, f"bench:account:{idx}"))


def _group_id(idx: int) -> str:
    return str(uuid5(NAMESPACE_URL, f"bench:group:{idx}"))


def _category_id(idx: int) -> str:
    return str(uuid5(NAMESPACE_URL, f"bench:category:{idx}"))


def _valuation_id(idx: int) -> str:
    return str(uuid5(NAMESPACE_URL, f"bench:valuation:{idx}"))


def _month_start(base_year: int, month_offset: int) -> date:
    y = base_year + (month_offset - 1) // 12
    m = ((month_offset - 1) % 12) + 1
    return date(y, m, 1)


def _days_in_month(d: date) -> int:
    if d.month == 12:
        return (date(d.year + 1, 1, 1) - d).days
    return (date(d.year, d.month + 1, 1) - d).days


def build_synthetic_dataset(config: SyntheticDatasetConfig) -> ParsedImportBundle:
    rng = _seeded_rng(config.seed)

    base_year = 2025

    groups: list[ParsedGroup] = []
    categories: list[ParsedCategory] = []
    accounts: list[ParsedAccount] = []
    transactions: list[ParsedTransaction] = []
    allocations: list[ParsedAllocation] = []
    valuations: list[ParsedValuation] = []

    # Build groups: evenly distribute categories across groups
    num_groups = max(1, config.num_categories // 5)
    for g in range(num_groups):
        group_id = _group_id(g)
        groups.append(
            ParsedGroup(
                group_id=group_id,
                name=f"Group {g}",
                sort_order=g * 10,
                is_hidden=False,
                is_system=False,
                is_deletable=True,
            )
        )

    # Build categories, spread across groups
    for c in range(config.num_categories - 1):
        group_idx = c % num_groups
        categories.append(
            ParsedCategory(
                category_id=_category_id(c),
                group_name=groups[group_idx].name,
                name=f"Category {c}",
                category_kind=CATEGORY_KIND_STANDARD,
                sort_order=c * 10,
                is_hidden=False,
                is_active=True,
                target_amount_minor=rng.randint(10000, 100000) * 100,
                due_date_rule=None,
                linked_account_name=None,
            )
        )

    # Add a credit card payment category
    cc_cat_id = _category_id(config.num_categories - 1)
    categories.append(
        ParsedCategory(
            category_id=cc_cat_id,
            group_name=f"Group {config.num_categories % num_groups}",
            name="Credit Card Payment",
            category_kind=CATEGORY_KIND_CREDIT_CARD_PAYMENT,
            sort_order=9999,
            is_hidden=False,
            is_active=True,
            target_amount_minor=None,
            due_date_rule=None,
            linked_account_name=None,
        )
    )

    # Build accounts: mostly budget, some tracking
    for a in range(config.num_accounts):
        is_budget = a < config.num_accounts - 2
        is_cc = is_budget and a % 3 == 2 and a > 0
        accounts.append(
            ParsedAccount(
                account_id=_account_id(a),
                name=f"Account {a}",
                account_class=ACCOUNT_CLASS_BUDGET if is_budget else ACCOUNT_CLASS_TRACKING_BALANCE,
                is_hidden=False,
                is_active=True,
                budget_account_type=(
                    BUDGET_ACCOUNT_TYPE_CREDIT_CARD
                    if is_cc
                    else (BUDGET_ACCOUNT_TYPE_DEPOSIT if is_budget else None)
                ),
                linked_payment_category_name=(
                    "Credit Card Payment" if is_cc else None
                ),
                display_liability_positive=is_cc,
            )
        )

    # Build transactions
    budget_account_indices = [
        i for i, a in enumerate(accounts) if a.account_class == ACCOUNT_CLASS_BUDGET
    ]
    category_indices = list(range(config.num_categories))

    # Create a starting balance transaction for each budget account
    for a_idx in budget_account_indices:
        transactions.append(
            ParsedTransaction(
                transaction_id=str(uuid4()),
                date=_month_start(base_year, 1),
                account_name=accounts[a_idx].name,
                amount_minor=rng.randint(50000, 500000) * 100,
                category_name=None,
                system_category=SYSTEM_CATEGORY_STARTING_BALANCE,
                status=STATUS_CLEARED,
                memo="Starting balance",
            )
        )

    # Distribute transactions across months
    tx_per_month = max(
        1,
        (config.num_transactions - len(budget_account_indices))
        // config.num_months,
    )
    remaining = config.num_transactions - len(budget_account_indices)

    for month_offset in range(1, config.num_months + 1):
        ms = _month_start(base_year, month_offset)
        dim = _days_in_month(ms)

        is_last_month = month_offset == config.num_months
        count_this_month = remaining if is_last_month else min(tx_per_month, remaining)
        remaining -= count_this_month

        for _ in range(count_this_month):
            day = rng.randint(1, dim)
            tx_date = ms.replace(day=day)
            a_idx = rng.choice(budget_account_indices)
            is_inflow = rng.random() < 0.4

            if is_inflow:
                amount = rng.randint(100, 50000) * 100
                system_cat = None
                cat_name = categories[rng.choice(category_indices)].name
            else:
                amount = -rng.randint(100, 30000) * 100
                system_cat = SYSTEM_CATEGORY_ATB if rng.random() < 0.1 else None
                cat_name = (
                    None
                    if system_cat == SYSTEM_CATEGORY_ATB
                    else categories[rng.choice(category_indices)].name
                )

            transactions.append(
                ParsedTransaction(
                    transaction_id=str(uuid4()),
                    date=tx_date,
                    account_name=accounts[a_idx].name,
                    amount_minor=amount,
                    category_name=cat_name,
                    system_category=system_cat,
                    status=rng.choice([STATUS_CLEARED, STATUS_PENDING]),
                    memo="Benchmark tx",
                )
            )

    # Build allocations per month
    category_bucket_names = [c.name for c in categories]
    for month_offset in range(1, config.num_months + 1):
        ms = _month_start(base_year, month_offset)
        dim = _days_in_month(ms)
        for _ in range(config.num_allocations_per_month):
            day = rng.randint(1, dim)
            from_name = rng.choice(category_bucket_names)
            to_name = rng.choice(
                [n for n in category_bucket_names if n != from_name]
            )
            allocations.append(
                ParsedAllocation(
                    allocation_id=str(uuid4()),
                    date=ms.replace(day=day),
                    from_name=from_name,
                    to_name=to_name,
                    amount_minor=rng.randint(1000, 50000) * 100,
                    memo="Benchmark allocation",
                )
            )

    # Build net worth valuations: one per tracking account
    for v in range(config.num_net_worth_valuations):
        a_idx = rng.randint(0, config.num_accounts - 1)
        account = accounts[a_idx]
        valuations.append(
            ParsedValuation(
                valuation_id=_valuation_id(v),
                raw_name=account.name,
                normalized_name=account.name.casefold(),
                account_name=account.name,
                match_kind="",
                match_candidates=(),
                effective_date=_month_start(base_year, config.num_months),
                amount_minor=rng.randint(-500000, 2000000) * 100,
                notes="Benchmark net worth",
            )
        )

    return ParsedImportBundle(
        spreadsheet_id="benchmark-synthetic",
        spreadsheet_title=f"Benchmark {config.label}",
        source_kind="fixture",
        accounts=accounts,
        groups=groups,
        categories=categories,
        transactions=transactions,
        allocations=allocations,
        valuations=valuations,
        expected={},
        discovered_named_ranges={},
    )


def describe_dataset(bundle: ParsedImportBundle) -> dict[str, Any]:
    accounts_by_class: dict[str, int] = {}
    for a in bundle.accounts:
        accounts_by_class[a.account_class] = (
            accounts_by_class.get(a.account_class, 0) + 1
        )
    categories_by_kind: dict[str, int] = {}
    for c in bundle.categories:
        categories_by_kind[c.category_kind] = (
            categories_by_kind.get(c.category_kind, 0) + 1
        )
    months: set[str] = set()
    for t in bundle.transactions:
        months.add(t.date.strftime("%Y-%m"))
    return {
        "accounts": len(bundle.accounts),
        "budget_accounts": accounts_by_class.get("BUDGET", 0),
        "tracking_accounts": accounts_by_class.get("TRACKING_BALANCE", 0),
        "groups": len(bundle.groups),
        "categories": len(bundle.categories),
        "standard_categories": categories_by_kind.get("STANDARD", 0),
        "cc_payment_categories": categories_by_kind.get("CREDIT_CARD_PAYMENT", 0),
        "transactions": len(bundle.transactions),
        "allocations": len(bundle.allocations),
        "valuations": len(bundle.valuations),
        "months": sorted(months),
    }
