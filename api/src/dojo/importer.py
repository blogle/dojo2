from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from typing import Any, cast
from urllib.parse import parse_qs, urlparse
from uuid import NAMESPACE_URL, uuid5

from dojo.constants import (
    ACCOUNT_CLASS_BUDGET,
    BUDGET_ACCOUNT_TYPE_CREDIT_CARD,
    BUDGET_ACCOUNT_TYPE_DEPOSIT,
    CATEGORY_KIND_CREDIT_CARD_PAYMENT,
    CATEGORY_KIND_STANDARD,
    GOOGLE_SHEETS_READONLY_SCOPE,
    STATUS_CLEARED,
    STATUS_PENDING,
    SYSTEM_CATEGORY_ATB,
    SYSTEM_CATEGORY_BALANCE_ADJUSTMENT,
    SYSTEM_CATEGORY_STARTING_BALANCE,
    SYSTEM_CATEGORY_TRANSFER,
)
from dojo.fixture_data import DEFAULT_FIXTURE
from dojo.money import parse_money_value, parse_signed_amount

IMPORTED_HIDDEN_CATEGORIES_GROUP_NAME = "Imported Hidden Categories"


class NamedRangeShape(StrEnum):
    COLUMN_VECTOR = "COLUMN_VECTOR"
    TABLE_BLOCK = "TABLE_BLOCK"
    SCALAR_OR_LABEL = "SCALAR_OR_LABEL"


class TransactionRowKind(StrEnum):
    REAL_TRANSACTION = "REAL_TRANSACTION"
    BLANK_ROW = "BLANK_ROW"
    BREAK_ROW = "BREAK_ROW"
    RECONCILIATION_ROW = "RECONCILIATION_ROW"
    IGNORED_HELPER_ROW = "IGNORED_HELPER_ROW"


NamedRangeMatrix = list[list[str]]


@dataclass(slots=True, frozen=True)
class NamedRangeContractEntry:
    logical_name: str
    aliases: tuple[str, ...]
    shape: NamedRangeShape
    required: bool
    semantic_role: str
    parser: str
    table: str | None = None


NAMED_RANGE_CONTRACT: tuple[NamedRangeContractEntry, ...] = (
    NamedRangeContractEntry(
        "transactions.date",
        ("trx_Dates",),
        NamedRangeShape.COLUMN_VECTOR,
        True,
        "transaction dates",
        "transaction_vectors",
        table="transactions",
    ),
    NamedRangeContractEntry(
        "transactions.outflow",
        ("trx_Outflows",),
        NamedRangeShape.COLUMN_VECTOR,
        True,
        "transaction outflows",
        "transaction_vectors",
        table="transactions",
    ),
    NamedRangeContractEntry(
        "transactions.inflow",
        ("trx_Inflows",),
        NamedRangeShape.COLUMN_VECTOR,
        True,
        "transaction inflows",
        "transaction_vectors",
        table="transactions",
    ),
    NamedRangeContractEntry(
        "transactions.category",
        ("trx_Categories",),
        NamedRangeShape.COLUMN_VECTOR,
        True,
        "transaction categories",
        "transaction_vectors",
        table="transactions",
    ),
    NamedRangeContractEntry(
        "transactions.account",
        ("trx_Accounts",),
        NamedRangeShape.COLUMN_VECTOR,
        True,
        "transaction accounts",
        "transaction_vectors",
        table="transactions",
    ),
    NamedRangeContractEntry(
        "transactions.memo",
        ("trx_Memos", "trx_Memo"),
        NamedRangeShape.COLUMN_VECTOR,
        True,
        "transaction memos",
        "transaction_vectors",
        table="transactions",
    ),
    NamedRangeContractEntry(
        "transactions.status",
        ("trx_Statuses", "trx_Status"),
        NamedRangeShape.COLUMN_VECTOR,
        True,
        "transaction statuses",
        "transaction_vectors",
        table="transactions",
    ),
    NamedRangeContractEntry(
        "allocations.date",
        ("cts_Dates",),
        NamedRangeShape.COLUMN_VECTOR,
        True,
        "allocation dates",
        "allocation_vectors",
        table="allocations",
    ),
    NamedRangeContractEntry(
        "allocations.amount",
        ("cts_Amounts",),
        NamedRangeShape.COLUMN_VECTOR,
        True,
        "allocation amounts",
        "allocation_vectors",
        table="allocations",
    ),
    NamedRangeContractEntry(
        "allocations.from",
        ("cts_FromCategories",),
        NamedRangeShape.COLUMN_VECTOR,
        True,
        "allocation source categories",
        "allocation_vectors",
        table="allocations",
    ),
    NamedRangeContractEntry(
        "allocations.to",
        ("cts_ToCategories",),
        NamedRangeShape.COLUMN_VECTOR,
        True,
        "allocation destination categories",
        "allocation_vectors",
        table="allocations",
    ),
    NamedRangeContractEntry(
        "allocations.memo",
        ("cts_Memos", "cts_Memo"),
        NamedRangeShape.COLUMN_VECTOR,
        False,
        "allocation memos",
        "allocation_vectors",
        table="allocations",
    ),
    NamedRangeContractEntry(
        "net_worth.date",
        ("ntw_Dates",),
        NamedRangeShape.COLUMN_VECTOR,
        True,
        "net worth dates",
        "net_worth_vectors",
        table="net_worth",
    ),
    NamedRangeContractEntry(
        "net_worth.amount",
        ("ntw_Amounts",),
        NamedRangeShape.COLUMN_VECTOR,
        True,
        "net worth amounts",
        "net_worth_vectors",
        table="net_worth",
    ),
    NamedRangeContractEntry(
        "net_worth.category",
        ("ntw_Categories", "ntw_NetWorthCategories"),
        NamedRangeShape.COLUMN_VECTOR,
        True,
        "net worth categories",
        "net_worth_vectors",
        table="net_worth",
    ),
    NamedRangeContractEntry(
        "net_worth.notes",
        ("ntw_Notes", "ntw_Comments"),
        NamedRangeShape.COLUMN_VECTOR,
        True,
        "net worth notes",
        "net_worth_vectors",
        table="net_worth",
    ),
    NamedRangeContractEntry(
        "config.deposit_accounts",
        ("cfg_Accounts",),
        NamedRangeShape.COLUMN_VECTOR,
        False,
        "deposit budget account names",
        "config_vectors",
    ),
    NamedRangeContractEntry(
        "config.credit_accounts",
        ("cfg_Cards",),
        NamedRangeShape.COLUMN_VECTOR,
        False,
        "credit card budget account names",
        "config_vectors",
    ),
    NamedRangeContractEntry(
        "config.credit_account_names",
        ("CreditCardAccounts",),
        NamedRangeShape.COLUMN_VECTOR,
        False,
        "credit card account names",
        "config_vectors",
    ),
    NamedRangeContractEntry(
        "config.account_entities",
        ("UserDefAccounts", "TransactionAccounts"),
        NamedRangeShape.COLUMN_VECTOR,
        False,
        "account entity names",
        "config_vectors",
    ),
    NamedRangeContractEntry(
        "config.hidden_accounts",
        ("HiddenAccounts", "UserDefHiddenAccounts"),
        NamedRangeShape.COLUMN_VECTOR,
        False,
        "hidden account names",
        "config_vectors",
    ),
    NamedRangeContractEntry(
        "config.category_names",
        ("UserDefCategories",),
        NamedRangeShape.COLUMN_VECTOR,
        True,
        "category names",
        "config_vectors",
        table="category_metadata",
    ),
    NamedRangeContractEntry(
        "config.configuration_data",
        ("r_ConfigurationData",),
        NamedRangeShape.TABLE_BLOCK,
        True,
        "configuration structure block",
        "table_block",
    ),
    NamedRangeContractEntry(
        "config.category_amounts",
        ("UserDefAmounts",),
        NamedRangeShape.COLUMN_VECTOR,
        False,
        "category target amounts",
        "config_vectors",
        table="category_metadata",
    ),
    NamedRangeContractEntry(
        "config.category_goals",
        ("UserDefGoals",),
        NamedRangeShape.COLUMN_VECTOR,
        False,
        "category goal metadata",
        "config_vectors",
        table="category_metadata",
    ),
    NamedRangeContractEntry(
        "config.category_linked_accounts",
        ("UserDefLinkedAccounts", "UserDefCreditCardLinkedAccounts"),
        NamedRangeShape.COLUMN_VECTOR,
        False,
        "category linked accounts",
        "config_vectors",
        table="category_metadata",
    ),
    NamedRangeContractEntry(
        "config.hidden_categories",
        ("HiddenCategories", "UserDefHiddenCategories"),
        NamedRangeShape.COLUMN_VECTOR,
        False,
        "hidden category names",
        "config_vectors",
    ),
    NamedRangeContractEntry(
        "config.net_worth_debts",
        ("NetWorthDebts",),
        NamedRangeShape.COLUMN_VECTOR,
        False,
        "net worth debt categories",
        "config_vectors",
    ),
    NamedRangeContractEntry(
        "labels.available_to_budget",
        ("v_AtoB",),
        NamedRangeShape.SCALAR_OR_LABEL,
        True,
        "available-to-budget label",
        "scalar_label",
    ),
    NamedRangeContractEntry(
        "labels.account_transfer",
        ("v_AccountTransfer",),
        NamedRangeShape.SCALAR_OR_LABEL,
        True,
        "account transfer label",
        "scalar_label",
    ),
    NamedRangeContractEntry(
        "labels.balance_adjustment",
        ("v_BalanceAdjustment",),
        NamedRangeShape.SCALAR_OR_LABEL,
        True,
        "balance adjustment label",
        "scalar_label",
    ),
    NamedRangeContractEntry(
        "labels.starting_balance",
        ("v_StartingBalance",),
        NamedRangeShape.SCALAR_OR_LABEL,
        True,
        "starting balance label",
        "scalar_label",
    ),
    NamedRangeContractEntry(
        "labels.approved_symbol",
        ("v_ApprovedSymbol",),
        NamedRangeShape.SCALAR_OR_LABEL,
        True,
        "approved status symbol",
        "scalar_label",
    ),
    NamedRangeContractEntry(
        "labels.pending_symbol",
        ("v_PendingSymbol",),
        NamedRangeShape.SCALAR_OR_LABEL,
        True,
        "pending status symbol",
        "scalar_label",
    ),
    NamedRangeContractEntry(
        "labels.break_symbol",
        ("v_BreakSymbol",),
        NamedRangeShape.SCALAR_OR_LABEL,
        True,
        "break row symbol",
        "scalar_label",
    ),
    NamedRangeContractEntry(
        "labels.category_group_symbol",
        ("v_CategoryGroupSymbol",),
        NamedRangeShape.SCALAR_OR_LABEL,
        True,
        "category group row symbol",
        "scalar_label",
    ),
    NamedRangeContractEntry(
        "labels.reportable_category_symbol",
        ("v_ReportableCategorySymbol",),
        NamedRangeShape.SCALAR_OR_LABEL,
        True,
        "reportable category row symbol",
        "scalar_label",
    ),
    NamedRangeContractEntry(
        "labels.non_reportable_category_symbol",
        ("v_NonReportableCategorySymbol",),
        NamedRangeShape.SCALAR_OR_LABEL,
        False,
        "non-reportable category row symbol",
        "scalar_label",
    ),
    NamedRangeContractEntry(
        "labels.debt_payment_category_symbol",
        ("v_DebtAccountSymbol",),
        NamedRangeShape.SCALAR_OR_LABEL,
        True,
        "debt or credit-card payment category row symbol",
        "scalar_label",
    ),
)

CONTRACT_BY_LOGICAL_NAME = {entry.logical_name: entry for entry in NAMED_RANGE_CONTRACT}
REQUIRED_NAMED_RANGES: tuple[str, ...] = tuple(
    entry.logical_name for entry in NAMED_RANGE_CONTRACT if entry.required
)


@dataclass(slots=True)
class ParsedAccount:
    account_id: str
    name: str
    account_class: str
    is_hidden: bool
    is_active: bool
    budget_account_type: str | None
    linked_payment_category_name: str | None
    display_liability_positive: bool


@dataclass(slots=True)
class ParsedGroup:
    group_id: str
    name: str
    sort_order: int
    is_hidden: bool
    is_system: bool
    is_deletable: bool


@dataclass(slots=True)
class ParsedCategory:
    category_id: str
    group_name: str
    name: str
    category_kind: str
    sort_order: int
    is_hidden: bool
    is_active: bool
    target_amount_minor: int | None
    due_date_rule: str | None
    linked_account_name: str | None


@dataclass(slots=True)
class ParsedTransaction:
    transaction_id: str
    date: date
    account_name: str
    amount_minor: int
    category_name: str | None
    system_category: str | None
    status: str
    memo: str


@dataclass(slots=True)
class ParsedAllocation:
    allocation_id: str
    date: date
    from_name: str
    to_name: str
    amount_minor: int
    memo: str


@dataclass(slots=True)
class ParsedValuation:
    valuation_id: str
    raw_name: str
    normalized_name: str
    account_name: str | None
    match_kind: str
    match_candidates: tuple[str, ...]
    effective_date: date
    amount_minor: int
    notes: str


@dataclass(slots=True)
class ParsedImportBundle:
    spreadsheet_id: str
    spreadsheet_title: str
    source_kind: str
    accounts: list[ParsedAccount]
    groups: list[ParsedGroup]
    categories: list[ParsedCategory]
    transactions: list[ParsedTransaction]
    allocations: list[ParsedAllocation]
    valuations: list[ParsedValuation]
    expected: dict[str, Any]
    discovered_named_ranges: dict[str, str]


@dataclass(slots=True)
class ResolvedNamedRange:
    contract: NamedRangeContractEntry
    actual_name: str
    matrix: NamedRangeMatrix


@dataclass(slots=True, frozen=True)
class ScalarLabelSet:
    available_to_budget: str
    account_transfer: str
    balance_adjustment: str
    starting_balance: str
    approved_symbol: str
    pending_symbol: str
    break_symbol: str


@dataclass(slots=True, frozen=True)
class ConfigurationRowSymbolSet:
    group: str
    reportable_category: str
    debt_payment_category: str
    non_reportable_category: str | None


@dataclass(slots=True)
class NamedRangeAccess:
    resolved_by_logical: dict[str, ResolvedNamedRange]
    discovered_named_ranges: dict[str, str]

    def require_vector(self, logical_name: str) -> list[str]:
        resolved = self._require(logical_name)
        return read_column_vector(resolved.contract, resolved.matrix)

    def optional_vector(self, logical_name: str) -> list[str] | None:
        resolved = self.resolved_by_logical.get(logical_name)
        if resolved is None:
            return None
        return read_column_vector(resolved.contract, resolved.matrix)

    def require_block(self, logical_name: str) -> NamedRangeMatrix:
        resolved = self._require(logical_name)
        return read_table_block(resolved.contract, resolved.matrix)

    def optional_block(self, logical_name: str) -> NamedRangeMatrix | None:
        resolved = self.resolved_by_logical.get(logical_name)
        if resolved is None:
            return None
        return read_table_block(resolved.contract, resolved.matrix)

    def require_scalar(self, logical_name: str) -> str:
        resolved = self._require(logical_name)
        return read_scalar_value(resolved.contract, resolved.matrix)

    def optional_scalar(self, logical_name: str) -> str | None:
        resolved = self.resolved_by_logical.get(logical_name)
        if resolved is None:
            return None
        return read_scalar_value(resolved.contract, resolved.matrix)

    def optional_name_set(self, logical_name: str) -> set[str]:
        vector = self.optional_vector(logical_name)
        if vector is None:
            return set()
        return {value.strip() for value in vector if value.strip()}

    def scalar_labels(self) -> ScalarLabelSet:
        return ScalarLabelSet(
            available_to_budget=self.require_scalar("labels.available_to_budget"),
            account_transfer=self.require_scalar("labels.account_transfer"),
            balance_adjustment=self.require_scalar("labels.balance_adjustment"),
            starting_balance=self.require_scalar("labels.starting_balance"),
            approved_symbol=self.require_scalar("labels.approved_symbol"),
            pending_symbol=self.require_scalar("labels.pending_symbol"),
            break_symbol=self.require_scalar("labels.break_symbol"),
        )

    def _require(self, logical_name: str) -> ResolvedNamedRange:
        resolved = self.resolved_by_logical.get(logical_name)
        if resolved is None:
            raise ValueError(f"Missing required named range mapping for {logical_name}")
        return resolved


def fixture_bundle() -> ParsedImportBundle:
    fixture = cast(dict[str, Any], DEFAULT_FIXTURE)
    return parse_named_range_workbook(
        spreadsheet_id=cast(str, fixture["spreadsheet_id"]),
        spreadsheet_title=cast(str, fixture["spreadsheet_title"]),
        named_ranges=cast(dict[str, NamedRangeMatrix], fixture["named_ranges"]),
        source_kind="fixture",
        expected=cast(dict[str, Any], fixture["expected"]),
    )


def extract_sheet_id(raw: str) -> str:
    value = raw.strip()
    if not value:
        raise ValueError("Sheet URL or ID is required")

    if value.startswith("fixture://"):
        return value.removeprefix("fixture://")

    if "/spreadsheets/d/" in value:
        path = urlparse(value).path
        marker = "/spreadsheets/d/"
        return path.split(marker, maxsplit=1)[1].split("/", maxsplit=1)[0]

    parsed = urlparse(value)
    if parsed.query:
        query = parse_qs(parsed.query)
        if "id" in query and query["id"]:
            return query["id"][0]

    return value


def parse_date_value(raw: str) -> date:
    value = raw.strip()
    if not value:
        raise ValueError("Date value is required")
    try:
        return date.fromisoformat(value)
    except ValueError:
        pass

    for separator in ("/", "-"):
        parts = value.split(separator)
        if len(parts) != 3:
            continue
        month, day, year = (part.strip() for part in parts)
        if not (month.isdigit() and day.isdigit() and year.isdigit()):
            continue
        return date(int(year), int(month), int(day))

    raise ValueError(f"Unsupported date value: {raw}")


def parse_status(
    raw: str,
    *,
    approved_symbol: str = "✅",
    pending_symbol: str = "🅿️",
    break_symbol: str | None = None,
) -> str:
    value = raw.strip()
    if value in {approved_symbol.strip(), "CLEARED"}:
        return STATUS_CLEARED
    if value in {pending_symbol.strip(), "PENDING"}:
        return STATUS_PENDING
    if break_symbol is not None and value == break_symbol.strip():
        raise ValueError(f"Break status symbol is not a transaction status: {raw}")
    raise ValueError(f"Unsupported status: {raw}")


def map_system_category(raw: str, labels: ScalarLabelSet | None = None) -> str | None:
    value = raw.strip().casefold()
    if labels is None:
        atb = "available to budget"
        starting_balance = "➡️ starting balance"
        account_transfer = "↕️ account transfer"
        balance_adjustment = "balance adjustment"
    else:
        atb = labels.available_to_budget.casefold()
        starting_balance = labels.starting_balance.casefold()
        account_transfer = labels.account_transfer.casefold()
        balance_adjustment = labels.balance_adjustment.casefold()

    if value == atb:
        return SYSTEM_CATEGORY_ATB
    if value == starting_balance or value == "starting balance":
        return SYSTEM_CATEGORY_STARTING_BALANCE
    if value == account_transfer or value == "account transfer":
        return SYSTEM_CATEGORY_TRANSFER
    if value == balance_adjustment or "balance adjustment" in value:
        return SYSTEM_CATEGORY_BALANCE_ADJUSTMENT
    return None


def normalize_named_range_name(name: str) -> str:
    return "".join(character for character in name.casefold() if character.isalnum())


def discover_named_ranges(available_names: list[str]) -> dict[str, str]:
    normalized_actual_names = {
        normalize_named_range_name(actual_name): actual_name for actual_name in available_names
    }
    discovered: dict[str, str] = {}
    for entry in NAMED_RANGE_CONTRACT:
        for alias in entry.aliases:
            actual_name = normalized_actual_names.get(normalize_named_range_name(alias))
            if actual_name is not None:
                discovered[entry.logical_name] = actual_name
                break
    return discovered


def consumed_named_range_aliases() -> set[str]:
    return {
        normalize_named_range_name(alias)
        for entry in NAMED_RANGE_CONTRACT
        for alias in entry.aliases
    }


def validate_required_named_ranges(
    discovered_named_ranges: dict[str, str],
    required_ranges: tuple[str, ...] = REQUIRED_NAMED_RANGES,
) -> None:
    missing = sorted(
        logical_name
        for logical_name in required_ranges
        if logical_name not in discovered_named_ranges
    )
    if missing:
        raise ValueError(f"Missing required named ranges: {', '.join(missing)}")


def normalize_named_range_matrix(matrix: NamedRangeMatrix) -> NamedRangeMatrix:
    normalized_rows = [[str(cell) for cell in row] for row in matrix]
    max_columns = max((len(row) for row in normalized_rows), default=0)
    if max_columns == 0:
        return [[] for _ in normalized_rows]
    return [row + [""] * (max_columns - len(row)) for row in normalized_rows]


def classify_named_range_shape(matrix: NamedRangeMatrix) -> NamedRangeShape:
    normalized = normalize_named_range_matrix(matrix)
    column_count = max((len(row) for row in normalized), default=0)
    row_count = len(normalized)
    if row_count <= 1 and column_count <= 1:
        return NamedRangeShape.SCALAR_OR_LABEL
    if column_count <= 1:
        return NamedRangeShape.COLUMN_VECTOR
    return NamedRangeShape.TABLE_BLOCK


def validate_named_range_shape(
    contract: NamedRangeContractEntry, matrix: NamedRangeMatrix
) -> NamedRangeMatrix:
    normalized = normalize_named_range_matrix(matrix)
    column_count = max((len(row) for row in normalized), default=0)
    if contract.shape == NamedRangeShape.COLUMN_VECTOR and column_count > 1:
        raise ValueError(
            f"Named range {contract.aliases[0]} for {contract.logical_name} must be single-column"
        )
    if contract.shape == NamedRangeShape.TABLE_BLOCK and not _is_rectangular(normalized):
        raise ValueError(
            f"Named range {contract.aliases[0]} for {contract.logical_name} must be rectangular"
        )
    if contract.shape == NamedRangeShape.SCALAR_OR_LABEL and not normalized:
        raise ValueError(
            f"Named range {contract.aliases[0]} for {contract.logical_name} must resolve to a value"
        )
    return normalized


def read_column_vector(contract: NamedRangeContractEntry, matrix: NamedRangeMatrix) -> list[str]:
    validated = validate_named_range_shape(contract, matrix)
    return [row[0] if row else "" for row in validated]


def read_table_block(
    contract: NamedRangeContractEntry, matrix: NamedRangeMatrix
) -> NamedRangeMatrix:
    return validate_named_range_shape(contract, matrix)


def read_scalar_value(contract: NamedRangeContractEntry, matrix: NamedRangeMatrix) -> str:
    validated = validate_named_range_shape(contract, matrix)
    non_blank_values = [cell.strip() for row in validated for cell in row if cell.strip()]
    if not non_blank_values:
        raise ValueError(f"Named range {contract.aliases[0]} for {contract.logical_name} is blank")
    distinct_values = set(non_blank_values)
    if len(distinct_values) > 1:
        raise ValueError(
            f"Named range {contract.aliases[0]} for {contract.logical_name} has multiple values"
        )
    return non_blank_values[0]


def build_named_range_access(
    named_ranges: dict[str, NamedRangeMatrix],
    available_named_ranges: list[str] | None = None,
) -> NamedRangeAccess:
    actual_names = available_named_ranges or sorted(named_ranges.keys())
    discovered = discover_named_ranges(actual_names)
    validate_required_named_ranges(discovered)

    resolved: dict[str, ResolvedNamedRange] = {}
    for entry in NAMED_RANGE_CONTRACT:
        actual_name = discovered.get(entry.logical_name)
        if actual_name is None:
            continue
        matrix = named_ranges.get(actual_name)
        if matrix is None:
            raise ValueError(f"Named range {actual_name} was discovered but no values were fetched")
        resolved[entry.logical_name] = ResolvedNamedRange(
            contract=entry,
            actual_name=actual_name,
            matrix=validate_named_range_shape(entry, matrix),
        )
    return NamedRangeAccess(
        resolved_by_logical=resolved,
        discovered_named_ranges=discovered,
    )


def validate_compatible_lengths(table_name: str, columns: dict[str, list[str]]) -> int:
    if not columns:
        return 0
    max_length = max(len(values) for values in columns.values())
    return max_length


def zip_named_range_rows(table_name: str, columns: dict[str, list[str]]) -> list[dict[str, str]]:
    row_count = validate_compatible_lengths(table_name, columns)
    normalized_columns = {
        name: values + [""] * (row_count - len(values)) for name, values in columns.items()
    }
    column_names = list(columns.keys())
    return [
        {column_name: normalized_columns[column_name][index] for column_name in column_names}
        for index in range(row_count)
    ]


def parse_named_range_workbook(
    spreadsheet_id: str,
    spreadsheet_title: str,
    named_ranges: dict[str, NamedRangeMatrix],
    source_kind: str,
    expected: dict[str, Any] | None = None,
    available_named_ranges: list[str] | None = None,
) -> ParsedImportBundle:
    access = build_named_range_access(named_ranges, available_named_ranges)
    categories, groups = parse_configuration_categories_and_groups(access)
    accounts = parse_configuration_accounts(access, categories)
    transactions = parse_transactions_named_ranges(access)
    allocations = parse_allocations_named_ranges(access)
    categories, groups, transactions, allocations = reconcile_category_references(
        access=access,
        categories=categories,
        groups=groups,
        transactions=transactions,
        allocations=allocations,
    )
    valuations = parse_net_worth_named_ranges(access, accounts)

    return ParsedImportBundle(
        spreadsheet_id=spreadsheet_id,
        spreadsheet_title=spreadsheet_title,
        source_kind=source_kind,
        accounts=accounts,
        groups=groups,
        categories=categories,
        transactions=transactions,
        allocations=allocations,
        valuations=valuations,
        expected=expected or {},
        discovered_named_ranges=access.discovered_named_ranges,
    )


def parse_configuration_categories_and_groups(
    access: NamedRangeAccess,
) -> tuple[list[ParsedCategory], list[ParsedGroup]]:
    metadata_rows = zip_named_range_rows(
        "category_metadata",
        _vector_columns(
            access,
            required={"name": "config.category_names"},
            optional={
                "target_amount": "config.category_amounts",
                "goal_rule": "config.category_goals",
                "linked_account": "config.category_linked_accounts",
            },
        ),
    )
    if not metadata_rows:
        raise ValueError("No category metadata rows were found")

    category_metadata_by_name: dict[str, dict[str, str]] = {}
    for _offset, row in enumerate(metadata_rows, start=1):
        name = row["name"].strip()
        if not name:
            # Real sheets can carry extra padded or helper metadata cells after the visible
            # category list. Group membership comes from r_ConfigurationData, so unnamed
            # metadata rows are ignored instead of treated as structural import failures.
            continue
        if name in category_metadata_by_name:
            raise ValueError(f"Category metadata contains duplicate category name: {name}")
        category_metadata_by_name[name] = row

    structure_block = access.require_block("config.configuration_data")
    row_symbols = ConfigurationRowSymbolSet(
        group=access.require_scalar("labels.category_group_symbol").strip(),
        reportable_category=access.require_scalar("labels.reportable_category_symbol").strip(),
        debt_payment_category=access.require_scalar("labels.debt_payment_category_symbol").strip(),
        non_reportable_category=_none_if_blank(
            access.optional_scalar("labels.non_reportable_category_symbol") or ""
        ),
    )
    hidden_categories = access.optional_name_set("config.hidden_categories")
    categories: list[ParsedCategory] = []
    ordered_group_names: list[str] = []
    payment_group_names: set[str] = set()
    current_group_name: str | None = None
    category_sort_index = 0

    category_symbols = {
        row_symbols.reportable_category: CATEGORY_KIND_STANDARD,
        row_symbols.debt_payment_category: CATEGORY_KIND_CREDIT_CARD_PAYMENT,
    }
    if row_symbols.non_reportable_category is not None:
        category_symbols[row_symbols.non_reportable_category] = CATEGORY_KIND_STANDARD

    for offset, raw_row in enumerate(structure_block, start=1):
        symbol = raw_row[0].strip() if raw_row else ""
        name = raw_row[1].strip() if len(raw_row) > 1 else ""
        if not symbol and not name and not any(cell.strip() for cell in raw_row[2:]):
            continue

        if symbol == row_symbols.group:
            if not name:
                raise ValueError(f"Configuration row {offset} is missing the category group name")
            current_group_name = name
            if name not in ordered_group_names:
                ordered_group_names.append(name)
            continue

        category_kind = category_symbols.get(symbol)
        if category_kind is None:
            raise ValueError(f"Unsupported configuration row symbol {symbol!r} on row {offset}")
        if current_group_name is None:
            raise ValueError(
                f"Configuration row {offset} defines category {name!r} before any group row"
            )
        if not name:
            raise ValueError(f"Configuration row {offset} is missing the category name")

        metadata = category_metadata_by_name.get(name)
        if metadata is None:
            raise ValueError(
                f"Category {name} is present in r_ConfigurationData but missing metadata"
            )

        linked_account_name = _none_if_blank(metadata.get("linked_account", ""))
        if category_kind == CATEGORY_KIND_CREDIT_CARD_PAYMENT:
            payment_group_names.add(current_group_name)
        category_sort_index += 1
        categories.append(
            ParsedCategory(
                category_id=_stable_id("category", name),
                group_name=current_group_name,
                name=name,
                category_kind=category_kind,
                sort_order=category_sort_index * 10,
                is_hidden=name in hidden_categories,
                is_active=True,
                target_amount_minor=parse_money_value(metadata.get("target_amount", "")),
                due_date_rule=_none_if_blank(metadata.get("goal_rule", "")),
                linked_account_name=linked_account_name,
            )
        )

    group_rows = _build_group_rows(ordered_group_names, payment_group_names)
    return categories, group_rows


def parse_configuration_accounts(
    access: NamedRangeAccess, categories: list[ParsedCategory]
) -> list[ParsedAccount]:
    hidden_accounts = access.optional_name_set("config.hidden_accounts")
    deposit_accounts = access.optional_vector("config.deposit_accounts") or []
    credit_accounts = access.optional_vector("config.credit_accounts") or []
    explicit_credit_accounts = access.optional_vector("config.credit_account_names") or []
    account_entities = access.optional_vector("config.account_entities") or []

    ordered_account_names = _ordered_non_blank(
        deposit_accounts,
        credit_accounts,
        explicit_credit_accounts,
        account_entities,
        access.require_vector("transactions.account"),
    )
    if not ordered_account_names:
        raise ValueError(
            "No account names were discovered from configuration or transaction ranges"
        )

    credit_name_set = {
        value.strip() for value in [*credit_accounts, *explicit_credit_accounts] if value.strip()
    }
    payment_category_by_account = {
        category.linked_account_name: category.name
        for category in categories
        if category.linked_account_name is not None
    }

    accounts: list[ParsedAccount] = []
    for name in ordered_account_names:
        is_credit_card = name in credit_name_set
        payment_category_name = payment_category_by_account.get(name)
        if is_credit_card and payment_category_name is None:
            inferred_payment_name = f"{name} Payment"
            if any(category.name == inferred_payment_name for category in categories):
                payment_category_name = inferred_payment_name
        accounts.append(
            ParsedAccount(
                account_id=_stable_id("account", name),
                name=name,
                account_class=ACCOUNT_CLASS_BUDGET,
                is_hidden=name in hidden_accounts,
                is_active=True,
                budget_account_type=(
                    BUDGET_ACCOUNT_TYPE_CREDIT_CARD
                    if is_credit_card
                    else BUDGET_ACCOUNT_TYPE_DEPOSIT
                ),
                linked_payment_category_name=payment_category_name,
                display_liability_positive=is_credit_card,
            )
        )
    return accounts


def parse_transactions_named_ranges(access: NamedRangeAccess) -> list[ParsedTransaction]:
    labels = access.scalar_labels()
    rows = zip_named_range_rows(
        "transactions",
        _vector_columns(
            access,
            required={
                "date": "transactions.date",
                "outflow": "transactions.outflow",
                "inflow": "transactions.inflow",
                "category": "transactions.category",
                "account": "transactions.account",
                "memo": "transactions.memo",
                "status": "transactions.status",
            },
            optional={},
        ),
    )

    records: list[ParsedTransaction] = []
    last_transaction_date_raw: str | None = None
    for offset, row in enumerate(rows, start=1):
        row_kind = classify_transaction_row(row, labels)
        if row_kind != TransactionRowKind.REAL_TRANSACTION:
            continue

        inflow = row["inflow"].strip()
        outflow = row["outflow"].strip()

        date_raw = row["date"].strip()
        if not date_raw and last_transaction_date_raw is not None:
            date_raw = last_transaction_date_raw
        account_name = row["account"].strip()
        category_raw = row["category"].strip()
        status_raw = row["status"].strip()
        if not date_raw or not account_name or not status_raw:
            raise ValueError(f"Meaningful transaction row {offset} is missing required fields")

        amount_minor = parse_signed_amount(inflow, outflow)
        system_category = map_system_category(category_raw, labels)
        category_name = _none_if_blank(category_raw)
        if system_category is not None:
            category_name = None
        last_transaction_date_raw = date_raw
        records.append(
            ParsedTransaction(
                transaction_id=_stable_id(
                    "transaction",
                    f"{date_raw}:{account_name}:{category_raw}:{row['memo'].strip()}:{offset}",
                ),
                date=parse_date_value(date_raw),
                account_name=account_name,
                amount_minor=amount_minor,
                category_name=category_name,
                system_category=system_category,
                status=parse_status(
                    status_raw,
                    approved_symbol=labels.approved_symbol,
                    pending_symbol=labels.pending_symbol,
                    break_symbol=labels.break_symbol,
                ),
                memo=row["memo"].strip(),
            )
        )
    return records


def reconcile_category_references(
    *,
    access: NamedRangeAccess,
    categories: list[ParsedCategory],
    groups: list[ParsedGroup],
    transactions: list[ParsedTransaction],
    allocations: list[ParsedAllocation],
) -> tuple[
    list[ParsedCategory], list[ParsedGroup], list[ParsedTransaction], list[ParsedAllocation]
]:
    canonical_by_normalized = {
        normalize_category_reference_name(category.name): category.name for category in categories
    }
    hidden_category_names = access.optional_name_set("config.hidden_categories")
    normalized_hidden_category_names = {
        normalize_category_reference_name(name) for name in hidden_category_names
    }

    for transaction in transactions:
        if transaction.category_name is None:
            continue
        normalized = normalize_category_reference_name(transaction.category_name)
        canonical = canonical_by_normalized.get(normalized)
        if canonical is not None:
            transaction.category_name = canonical

    for allocation in allocations:
        for attribute_name in ("from_name", "to_name"):
            raw_name = getattr(allocation, attribute_name)
            if raw_name == "Available to budget":
                continue
            normalized = normalize_category_reference_name(raw_name)
            canonical = canonical_by_normalized.get(normalized)
            if canonical is not None:
                setattr(allocation, attribute_name, canonical)

    referenced_names = {
        transaction.category_name
        for transaction in transactions
        if transaction.category_name is not None
    }
    for allocation in allocations:
        if allocation.from_name != "Available to budget":
            referenced_names.add(allocation.from_name)
        if allocation.to_name != "Available to budget":
            referenced_names.add(allocation.to_name)

    known_category_names = {category.name for category in categories}
    missing_category_names = sorted(
        name for name in referenced_names if name not in known_category_names
    )
    if not missing_category_names:
        return categories, groups, transactions, allocations

    group_names = {group.name for group in groups}
    if IMPORTED_HIDDEN_CATEGORIES_GROUP_NAME not in group_names:
        groups.append(
            ParsedGroup(
                group_id=_stable_id("group", IMPORTED_HIDDEN_CATEGORIES_GROUP_NAME),
                name=IMPORTED_HIDDEN_CATEGORIES_GROUP_NAME,
                sort_order=(len(groups) + 1) * 10,
                is_hidden=True,
                is_system=True,
                is_deletable=False,
            )
        )

    next_sort_order = (
        max((category.sort_order for category in categories), default=0) // 10 + 1
    ) * 10
    for name in missing_category_names:
        categories.append(
            ParsedCategory(
                category_id=_stable_id("category", name),
                group_name=IMPORTED_HIDDEN_CATEGORIES_GROUP_NAME,
                name=name,
                category_kind=CATEGORY_KIND_STANDARD,
                sort_order=next_sort_order,
                is_hidden=normalize_category_reference_name(name)
                in normalized_hidden_category_names,
                is_active=False,
                target_amount_minor=None,
                due_date_rule=None,
                linked_account_name=None,
            )
        )
        next_sort_order += 10

    return categories, groups, transactions, allocations


def classify_transaction_row(row: dict[str, str], labels: ScalarLabelSet) -> TransactionRowKind:
    if _row_is_blank(row):
        return TransactionRowKind.BLANK_ROW
    if _is_break_row(row, labels.break_symbol):
        return TransactionRowKind.BREAK_ROW

    inflow = row.get("inflow", "").strip()
    outflow = row.get("outflow", "").strip()
    date_raw = row.get("date", "").strip()
    account_name = row.get("account", "").strip()
    category_raw = row.get("category", "").strip()
    status_raw = row.get("status", "").strip()
    memo = row.get("memo", "").strip()

    if (
        (inflow or outflow)
        and not account_name
        and not category_raw
        and status_raw == labels.pending_symbol.strip()
    ):
        return TransactionRowKind.IGNORED_HELPER_ROW
    if inflow or outflow:
        return TransactionRowKind.REAL_TRANSACTION

    known_status_values = {
        labels.approved_symbol.strip(),
        labels.pending_symbol.strip(),
        labels.break_symbol.strip(),
        STATUS_CLEARED,
        STATUS_PENDING,
    }
    has_system_category = bool(
        category_raw and map_system_category(category_raw, labels) is not None
    )
    has_known_status = status_raw in known_status_values
    has_reconciliation_signals = any([date_raw, account_name, category_raw, status_raw]) and (
        bool(date_raw) or has_known_status or has_system_category
    )
    if has_reconciliation_signals:
        return TransactionRowKind.RECONCILIATION_ROW
    if memo or any([date_raw, account_name, category_raw, status_raw]):
        return TransactionRowKind.IGNORED_HELPER_ROW
    return TransactionRowKind.BLANK_ROW


def parse_allocations_named_ranges(access: NamedRangeAccess) -> list[ParsedAllocation]:
    labels = access.scalar_labels()
    rows = zip_named_range_rows(
        "allocations",
        _vector_columns(
            access,
            required={
                "date": "allocations.date",
                "amount": "allocations.amount",
                "from_name": "allocations.from",
                "to_name": "allocations.to",
            },
            optional={"memo": "allocations.memo"},
        ),
    )

    records: list[ParsedAllocation] = []
    for offset, row in enumerate(rows, start=1):
        if _row_is_blank(row):
            continue

        date_raw = row["date"].strip()
        amount_raw = row["amount"].strip()
        from_name = _normalize_bucket_name(row["from_name"].strip(), labels)
        to_name = _normalize_bucket_name(row["to_name"].strip(), labels)
        if not date_raw or not amount_raw or not from_name or not to_name:
            raise ValueError(f"Meaningful allocation row {offset} is missing required fields")
        if from_name == to_name:
            raise ValueError(f"Allocation row {offset} must move between different buckets")

        amount_minor = parse_money_value(amount_raw)
        if amount_minor is None or amount_minor < 0:
            raise ValueError(f"Allocation row {offset} must contain a positive amount")
        if amount_minor == 0:
            continue

        records.append(
            ParsedAllocation(
                allocation_id=_stable_id(
                    "allocation",
                    f"{date_raw}:{from_name}:{to_name}:{row.get('memo', '').strip()}:{offset}",
                ),
                date=parse_date_value(date_raw),
                from_name=from_name,
                to_name=to_name,
                amount_minor=amount_minor,
                memo=row.get("memo", "").strip(),
            )
        )
    return records


def parse_net_worth_named_ranges(
    access: NamedRangeAccess, accounts: list[ParsedAccount]
) -> list[ParsedValuation]:
    rows = zip_named_range_rows(
        "net_worth",
        _vector_columns(
            access,
            required={
                "date": "net_worth.date",
                "amount": "net_worth.amount",
                "raw_name": "net_worth.category",
                "notes": "net_worth.notes",
            },
            optional={},
        ),
    )
    account_names = {account.name for account in accounts}
    account_names_by_normalized: dict[str, list[str]] = {}
    for account in accounts:
        normalized_account_name = normalize_financial_entity_name(account.name)
        account_names_by_normalized.setdefault(normalized_account_name, []).append(account.name)
    debt_names = access.optional_name_set("config.net_worth_debts")
    normalized_debt_names = {
        normalize_financial_entity_name(name)
        for name in debt_names
        if normalize_financial_entity_name(name)
    }

    records: list[ParsedValuation] = []
    for offset, row in enumerate(rows, start=1):
        if _row_is_blank(row):
            continue

        date_raw = row["date"].strip()
        amount_raw = row["amount"].strip()
        raw_name = row["raw_name"].strip()
        if not date_raw or not amount_raw or not raw_name:
            raise ValueError(f"Meaningful net worth row {offset} is missing required fields")

        amount_minor = parse_money_value(amount_raw)
        if amount_minor is None:
            raise ValueError(f"Net worth row {offset} contains an invalid amount")
        normalized_name = normalize_financial_entity_name(raw_name)
        if (
            raw_name in debt_names or normalized_name in normalized_debt_names
        ) and amount_minor > 0:
            amount_minor = -amount_minor

        account_name: str | None = None
        match_kind = "TRACKING_ONLY"
        match_candidates: tuple[str, ...] = ()
        if raw_name in account_names:
            account_name = raw_name
            match_kind = "EXACT_BUDGET_ACCOUNT"
        else:
            normalized_candidates = account_names_by_normalized.get(normalized_name, [])
            if len(normalized_candidates) == 1:
                account_name = normalized_candidates[0]
                match_kind = "NORMALIZED_BUDGET_ACCOUNT"
            elif len(normalized_candidates) > 1:
                match_kind = "AMBIGUOUS_BUDGET_ACCOUNT"
                match_candidates = tuple(sorted(normalized_candidates))

        records.append(
            ParsedValuation(
                valuation_id=_stable_id("valuation", f"{date_raw}:{raw_name}:{offset}"),
                raw_name=raw_name,
                normalized_name=normalized_name,
                account_name=account_name,
                match_kind=match_kind,
                match_candidates=match_candidates,
                effective_date=parse_date_value(date_raw),
                amount_minor=amount_minor,
                notes=row["notes"].strip(),
            )
        )
    return records


def _build_group_rows(
    ordered_group_names: list[str], payment_group_names: set[str]
) -> list[ParsedGroup]:
    groups: list[ParsedGroup] = []
    for index, name in enumerate(ordered_group_names):
        is_payment_group = name in payment_group_names
        groups.append(
            ParsedGroup(
                group_id=_stable_id("group", name),
                name=name,
                sort_order=(index + 1) * 10,
                is_hidden=False,
                is_system=is_payment_group,
                is_deletable=not is_payment_group,
            )
        )
    return groups


def _vector_columns(
    access: NamedRangeAccess,
    *,
    required: dict[str, str],
    optional: dict[str, str],
) -> dict[str, list[str]]:
    columns = {key: access.require_vector(logical_name) for key, logical_name in required.items()}
    for key, logical_name in optional.items():
        vector = access.optional_vector(logical_name)
        if vector is not None:
            columns[key] = vector
    return columns


def _ordered_non_blank(*vectors: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for vector in vectors:
        for value in vector:
            normalized = value.strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            ordered.append(normalized)
    return ordered


def _row_is_blank(row: dict[str, str]) -> bool:
    return not any(value.strip() for value in row.values())


def _is_break_row(row: dict[str, str], break_symbol: str) -> bool:
    status = row.get("status", "").strip()
    other_values = [
        row.get("date", "").strip(),
        row.get("outflow", "").strip(),
        row.get("inflow", "").strip(),
        row.get("category", "").strip(),
        row.get("account", "").strip(),
        row.get("memo", "").strip(),
    ]
    return status == break_symbol.strip() and not any(other_values)


def _normalize_bucket_name(raw_name: str, labels: ScalarLabelSet) -> str:
    if raw_name.casefold() == labels.available_to_budget.casefold():
        return "Available to budget"
    return raw_name


def normalize_category_reference_name(raw_name: str) -> str:
    return raw_name.strip().rstrip("\\/").casefold()


def normalize_financial_entity_name(raw_name: str) -> str:
    return "".join(character for character in raw_name.casefold() if character.isalnum())


def _none_if_blank(raw: str) -> str | None:
    value = raw.strip()
    return value or None


def _row_has_meaning(row: dict[str, str]) -> bool:
    return any(value.strip() for value in row.values())


def _is_rectangular(matrix: NamedRangeMatrix) -> bool:
    if not matrix:
        return True
    width = len(matrix[0])
    return all(len(row) == width for row in matrix)


def _stable_id(kind: str, value: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"dojo:{kind}:{value}"))


__all__ = [
    "CONTRACT_BY_LOGICAL_NAME",
    "GOOGLE_SHEETS_READONLY_SCOPE",
    "NAMED_RANGE_CONTRACT",
    "NamedRangeAccess",
    "NamedRangeContractEntry",
    "NamedRangeShape",
    "ParsedAccount",
    "ParsedAllocation",
    "ParsedCategory",
    "ParsedGroup",
    "ParsedImportBundle",
    "ParsedTransaction",
    "ParsedValuation",
    "REQUIRED_NAMED_RANGES",
    "ConfigurationRowSymbolSet",
    "ScalarLabelSet",
    "TransactionRowKind",
    "build_named_range_access",
    "classify_transaction_row",
    "classify_named_range_shape",
    "consumed_named_range_aliases",
    "discover_named_ranges",
    "extract_sheet_id",
    "fixture_bundle",
    "map_system_category",
    "normalize_financial_entity_name",
    "normalize_named_range_name",
    "parse_configuration_accounts",
    "parse_configuration_categories_and_groups",
    "parse_date_value",
    "parse_named_range_workbook",
    "parse_net_worth_named_ranges",
    "parse_status",
    "parse_transactions_named_ranges",
    "read_column_vector",
    "read_scalar_value",
    "read_table_block",
    "validate_compatible_lengths",
    "validate_named_range_shape",
    "validate_required_named_ranges",
    "zip_named_range_rows",
]
