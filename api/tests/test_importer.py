from __future__ import annotations

import pytest

from dojo.fixture_data import DEFAULT_FIXTURE, column, scalar
from dojo.importer import (
    CONTRACT_BY_LOGICAL_NAME,
    NAMED_RANGE_CONTRACT,
    NamedRangeContractEntry,
    NamedRangeShape,
    TransactionRowKind,
    build_named_range_access,
    classify_named_range_shape,
    classify_transaction_row,
    discover_named_ranges,
    extract_sheet_id,
    fixture_bundle,
    map_system_category,
    normalize_named_range_name,
    parse_configuration_accounts,
    parse_configuration_categories_and_groups,
    parse_date_value,
    parse_named_range_workbook,
    parse_net_worth_named_ranges,
    parse_status,
    parse_transactions_named_ranges,
    read_column_vector,
    read_scalar_value,
    read_table_block,
    validate_named_range_shape,
    validate_required_named_ranges,
    zip_named_range_rows,
)
from dojo.money import parse_signed_amount


def copy_named_ranges() -> dict[str, list[list[str]]]:
    return {key: [row[:] for row in value] for key, value in DEFAULT_FIXTURE["named_ranges"].items()}


def test_extract_sheet_id_from_url() -> None:
    raw = "https://docs.google.com/spreadsheets/d/abc123/edit#gid=0"
    assert extract_sheet_id(raw) == "abc123"


def test_parse_date_value() -> None:
    assert parse_date_value("2026-02-03").isoformat() == "2026-02-03"
    assert parse_date_value("1/1/2021").isoformat() == "2021-01-01"
    assert parse_date_value("01/02/2021").isoformat() == "2021-01-02"


def test_parse_status_symbol_mapping() -> None:
    assert parse_status("APP", approved_symbol="APP", pending_symbol="PEND") == "CLEARED"
    assert parse_status("PEND", approved_symbol="APP", pending_symbol="PEND") == "PENDING"


def test_system_category_mapping_from_scalar_labels() -> None:
    bundle = fixture_bundle()
    access = build_named_range_access(DEFAULT_FIXTURE["named_ranges"])
    labels = access.scalar_labels()
    assert map_system_category("ATB", labels) == "TX_AVAILABLE_TO_BUDGET"
    assert map_system_category("SB", labels) == "TX_STARTING_BALANCE"
    assert map_system_category("XFER", labels) == "TX_ACCOUNT_TRANSFER"
    assert map_system_category("BALADJ", labels) == "TX_BALANCE_ADJUSTMENT"
    assert bundle.discovered_named_ranges["labels.available_to_budget"] == "v_AtoB"


def test_named_range_name_normalization() -> None:
    assert normalize_named_range_name("trx_Dates") == "trxdates"
    assert normalize_named_range_name("User Def Accounts") == "userdefaccounts"


def test_named_range_discovery_and_contract_shape() -> None:
    discovered = discover_named_ranges(list(DEFAULT_FIXTURE["named_ranges"].keys()))
    assert discovered["transactions.date"] == "trx_Dates"
    assert discovered["labels.available_to_budget"] == "v_AtoB"


def test_required_named_range_validation() -> None:
    discovered = discover_named_ranges(list(DEFAULT_FIXTURE["named_ranges"].keys()))
    validate_required_named_ranges(discovered)


def test_shape_classification() -> None:
    assert classify_named_range_shape(column(["a", "b"])) == NamedRangeShape.COLUMN_VECTOR
    assert classify_named_range_shape([["a", "b"], ["c", "d"]]) == NamedRangeShape.TABLE_BLOCK
    assert classify_named_range_shape(scalar("x")) == NamedRangeShape.SCALAR_OR_LABEL


def test_scalar_reading() -> None:
    contract = CONTRACT_BY_LOGICAL_NAME["labels.available_to_budget"]
    assert read_scalar_value(contract, scalar("ATB")) == "ATB"


def test_table_block_acceptance() -> None:
    contract = NamedRangeContractEntry(
        logical_name="test.configuration_block",
        aliases=("r_ConfigurationData",),
        shape=NamedRangeShape.TABLE_BLOCK,
        required=False,
        semantic_role="configuration block",
        parser="table_block",
    )
    block = read_table_block(contract, DEFAULT_FIXTURE["named_ranges"]["r_ConfigurationData"])
    assert block[0][0] == "GROUP"
    assert block[1][1] == "Grocery"


def test_configuration_block_regression_is_not_sent_to_single_column_validator() -> None:
    contract = NamedRangeContractEntry(
        logical_name="test.configuration_block",
        aliases=("r_ConfigurationData",),
        shape=NamedRangeShape.TABLE_BLOCK,
        required=False,
        semantic_role="configuration block",
        parser="table_block",
    )
    matrix = DEFAULT_FIXTURE["named_ranges"]["r_ConfigurationData"]
    validated = validate_named_range_shape(contract, matrix)
    assert validated == matrix


def test_required_transaction_vector_fails_when_multicolumn() -> None:
    contract = CONTRACT_BY_LOGICAL_NAME["transactions.account"]
    with pytest.raises(ValueError, match="must be single-column"):
        read_column_vector(contract, [["Checking", "Extra"]])


def test_vector_padding_and_row_zipping_tolerate_trailing_blanks() -> None:
    rows = zip_named_range_rows(
        "transactions",
        {
            "date": ["2026-01-01", "2026-01-02"],
            "memo": ["one"],
        },
    )
    assert rows == [
        {"date": "2026-01-01", "memo": "one"},
        {"date": "2026-01-02", "memo": ""},
    ]


def test_transaction_row_zipping_and_break_row_skipping() -> None:
    access = build_named_range_access(DEFAULT_FIXTURE["named_ranges"])
    transactions = parse_transactions_named_ranges(access)
    assert len(transactions) == 12
    assert all(transaction.memo != "" or transaction.category_name is not None for transaction in transactions)


def test_transaction_row_classification_distinguishes_real_blank_break_and_helper_rows() -> None:
    access = build_named_range_access(DEFAULT_FIXTURE["named_ranges"])
    labels = access.scalar_labels()

    assert (
        classify_transaction_row(
            {
                "date": "2026-01-01",
                "outflow": "$10.00",
                "inflow": "",
                "category": "Category A",
                "account": "Account A",
                "memo": "Lunch",
                "status": labels.approved_symbol,
            },
            labels,
        )
        == TransactionRowKind.REAL_TRANSACTION
    )
    assert (
        classify_transaction_row(
            {
                "date": "",
                "outflow": "",
                "inflow": "",
                "category": "",
                "account": "",
                "memo": "",
                "status": "",
            },
            labels,
        )
        == TransactionRowKind.BLANK_ROW
    )
    assert (
        classify_transaction_row(
            {
                "date": "",
                "outflow": "",
                "inflow": "",
                "category": "",
                "account": "",
                "memo": "",
                "status": labels.break_symbol,
            },
            labels,
        )
        == TransactionRowKind.BREAK_ROW
    )
    assert (
        classify_transaction_row(
            {
                "date": "2026-01-31",
                "outflow": "",
                "inflow": "",
                "category": labels.available_to_budget,
                "account": "Account A",
                "memo": "Reconciled",
                "status": labels.approved_symbol,
            },
            labels,
        )
        == TransactionRowKind.RECONCILIATION_ROW
    )
    assert (
        classify_transaction_row(
            {
                "date": "",
                "outflow": "",
                "inflow": "",
                "category": "",
                "account": "",
                "memo": "UI helper",
                "status": "",
            },
            labels,
        )
        == TransactionRowKind.IGNORED_HELPER_ROW
    )


def test_transaction_parser_skips_reconciliation_and_helper_rows_without_amounts() -> None:
    named_ranges = copy_named_ranges()
    named_ranges["trx_Dates"][8] = ["2026-01-31"]
    named_ranges["trx_Categories"][8] = ["ATB"]
    named_ranges["trx_Accounts"][8] = ["Checking"]
    named_ranges["trx_Memos"][8] = ["Reconciliation marker"]
    named_ranges["trx_Statuses"][8] = ["APP"]
    named_ranges["trx_Dates"][13] = [""]
    named_ranges["trx_Categories"][13] = [""]
    named_ranges["trx_Accounts"][13] = [""]
    named_ranges["trx_Memos"][13] = ["Helper text"]
    named_ranges["trx_Statuses"][13] = [""]

    access = build_named_range_access(named_ranges)
    transactions = parse_transactions_named_ranges(access)

    assert len(transactions) == 12
    assert all(transaction.memo != "Reconciliation marker" for transaction in transactions)
    assert all(transaction.memo != "Helper text" for transaction in transactions)


def test_transaction_parser_skips_pending_staging_row_with_amount_but_no_account_or_category() -> None:
    named_ranges = copy_named_ranges()
    named_ranges["trx_Dates"][1] = ["2026-01-15"]
    named_ranges["trx_Outflows"][1] = [""]
    named_ranges["trx_Inflows"][1] = ["$25.00"]
    named_ranges["trx_Categories"][1] = [""]
    named_ranges["trx_Accounts"][1] = [""]
    named_ranges["trx_Memos"][1] = ["Pending imported row"]
    named_ranges["trx_Statuses"][1] = ["PEND"]

    access = build_named_range_access(named_ranges)
    transactions = parse_transactions_named_ranges(access)

    assert len(transactions) == 11
    assert all(transaction.memo != "Pending imported row" for transaction in transactions)


def test_amount_bearing_transaction_with_blank_category_imports_as_uncategorized() -> None:
    named_ranges = copy_named_ranges()
    named_ranges["trx_Categories"][0] = [""]

    access = build_named_range_access(named_ranges)
    transactions = parse_transactions_named_ranges(access)

    assert transactions[0].category_name is None
    assert transactions[0].system_category is None


def test_amount_bearing_transaction_with_blank_date_uses_previous_transaction_date() -> None:
    named_ranges = copy_named_ranges()
    named_ranges["trx_Dates"][1] = [""]

    access = build_named_range_access(named_ranges)
    transactions = parse_transactions_named_ranges(access)

    assert transactions[1].date.isoformat() == "2026-01-01"


def test_signed_money_conversion_from_named_ranges() -> None:
    assert parse_signed_amount("$12.34", "") == 1234
    assert parse_signed_amount("", "$12.34") == -1234


def test_named_range_import_extracts_hidden_entities() -> None:
    bundle = fixture_bundle()
    assert any(account.name == "Wallet" and account.is_hidden for account in bundle.accounts)
    assert any(category.name == "Secret Stash" and category.is_hidden for category in bundle.categories)
    assert any(group.name == "Credit Card Payments" and group.is_system for group in bundle.groups)


def test_config_import_from_semantic_ranges() -> None:
    access = build_named_range_access(DEFAULT_FIXTURE["named_ranges"])
    categories, groups = parse_configuration_categories_and_groups(access)
    accounts = parse_configuration_accounts(access, categories)
    assert [group.name for group in groups] == ["Living", "Bills", "Credit Card Payments"]
    assert [category.name for category in categories] == [
        "Grocery",
        "Secret Stash",
        "Utilities",
        "Reserve Card Payment",
    ]
    reserve_card = next(account for account in accounts if account.name == "Reserve Card")
    assert reserve_card.budget_account_type == "CREDIT_CARD"
    assert reserve_card.linked_payment_category_name == "Reserve Card Payment"


def test_configuration_block_drives_membership_and_order_not_flat_vectors() -> None:
    named_ranges = copy_named_ranges()
    named_ranges["UserDefCategories"] = column(
        ["Reserve Card Payment", "Utilities", "Grocery", "Secret Stash"]
    )
    named_ranges["UserDefAmounts"] = column(["", "$150.00", "$300.00", "$100.00"])
    named_ranges["UserDefGoals"] = column(["", "Monthly", "", ""])
    named_ranges["UserDefLinkedAccounts"] = column(["Reserve Card", "", "", ""])
    named_ranges["UserDefCategoryGroupNames"] = column(
        ["Wrong A", "Wrong B", "Wrong C", "Wrong D"]
    )

    access = build_named_range_access(named_ranges)
    categories, groups = parse_configuration_categories_and_groups(access)

    assert [group.name for group in groups] == ["Living", "Bills", "Credit Card Payments"]
    assert [(category.group_name, category.name) for category in categories] == [
        ("Living", "Grocery"),
        ("Living", "Secret Stash"),
        ("Bills", "Utilities"),
        ("Credit Card Payments", "Reserve Card Payment"),
    ]


def test_configuration_block_parsing_does_not_depend_on_fixture_category_names() -> None:
    named_ranges = copy_named_ranges()
    named_ranges["UserDefCategories"] = column(
        ["Category Alpha", "Category Beta", "Category Gamma", "Card Payment Alpha"]
    )
    named_ranges["UserDefAmounts"] = column(["$300.00", "$150.00", "$100.00", ""])
    named_ranges["UserDefGoals"] = column(["", "Monthly", "", ""])
    named_ranges["UserDefLinkedAccounts"] = column(["", "", "", "Reserve Card"])
    named_ranges["HiddenCategories"] = column(["Category Gamma"])
    named_ranges["r_ConfigurationData"] = [
        ["GROUP", "Group One", "", ""],
        ["CAT", "Category Alpha", "$300.00", ""],
        ["NRCAT", "Category Gamma", "$100.00", ""],
        ["GROUP", "Group Two", "", ""],
        ["CAT", "Category Beta", "$150.00", "Monthly"],
        ["GROUP", "Payment Group", "", ""],
        ["DEBT", "Card Payment Alpha", "", ""],
    ]

    access = build_named_range_access(named_ranges)
    categories, groups = parse_configuration_categories_and_groups(access)

    assert [group.name for group in groups] == ["Group One", "Group Two", "Payment Group"]
    assert [category.name for category in categories] == [
        "Category Alpha",
        "Category Gamma",
        "Category Beta",
        "Card Payment Alpha",
    ]
    assert next(category for category in categories if category.name == "Card Payment Alpha").category_kind == (
        "CREDIT_CARD_PAYMENT"
    )
    assert next(group for group in groups if group.name == "Payment Group").is_system is True


def test_category_metadata_rows_with_blank_names_are_ignored() -> None:
    named_ranges = copy_named_ranges()
    named_ranges["UserDefCategories"] = column(
        ["Grocery", "Utilities", "Secret Stash", "Reserve Card Payment", "", ""]
    )
    named_ranges["UserDefAmounts"] = column(["$300.00", "$150.00", "$100.00", "", "$99.00", ""])
    named_ranges["UserDefGoals"] = column(["", "Monthly", "", "", "Monthly", ""])
    named_ranges["UserDefLinkedAccounts"] = column(["", "", "", "Reserve Card", "Reserve Card", ""])

    access = build_named_range_access(named_ranges)
    categories, groups = parse_configuration_categories_and_groups(access)

    assert [group.name for group in groups] == ["Living", "Bills", "Credit Card Payments"]
    assert [category.name for category in categories] == [
        "Grocery",
        "Secret Stash",
        "Utilities",
        "Reserve Card Payment",
    ]


def test_transaction_category_reference_is_canonicalized_to_visible_category_name() -> None:
    named_ranges = copy_named_ranges()
    named_ranges["trx_Categories"][3] = ["Grocery\\"]

    bundle = parse_named_range_workbook(
        spreadsheet_id="fixture-default-sheet",
        spreadsheet_title="Copy of Finances 2.0",
        named_ranges=named_ranges,
        source_kind="fixture",
    )

    grocery_transaction = next(transaction for transaction in bundle.transactions if transaction.memo == "Groceries")
    assert grocery_transaction.category_name == "Grocery"


def test_hidden_legacy_transaction_category_is_synthesized_when_missing_from_visible_config() -> None:
    named_ranges = copy_named_ranges()
    named_ranges["trx_Categories"][3] = ["Legacy Hidden"]
    named_ranges["HiddenCategories"] = column(["Secret Stash", "Legacy Hidden"])

    bundle = parse_named_range_workbook(
        spreadsheet_id="fixture-default-sheet",
        spreadsheet_title="Copy of Finances 2.0",
        named_ranges=named_ranges,
        source_kind="fixture",
    )

    legacy_category = next(category for category in bundle.categories if category.name == "Legacy Hidden")
    legacy_group = next(group for group in bundle.groups if group.name == "Imported Hidden Categories")
    assert legacy_category.group_name == legacy_group.name
    assert legacy_category.is_hidden is True
    assert legacy_category.is_active is False
    assert legacy_group.is_system is True


def test_allocation_row_zipping() -> None:
    rows = parse_named_range_workbook(
        spreadsheet_id="fixture-default-sheet",
        spreadsheet_title="Copy of Finances 2.0",
        named_ranges=DEFAULT_FIXTURE["named_ranges"],
        source_kind="fixture",
    ).allocations
    assert rows[0].from_name == "Available to budget"
    assert rows[0].to_name == "Grocery"


def test_zero_amount_allocation_row_is_skipped() -> None:
    named_ranges = copy_named_ranges()
    named_ranges["cts_Amounts"][0] = ["$0.00"]

    bundle = parse_named_range_workbook(
        spreadsheet_id="fixture-default-sheet",
        spreadsheet_title="Copy of Finances 2.0",
        named_ranges=named_ranges,
        source_kind="fixture",
    )

    assert len(bundle.allocations) == 7


def test_net_worth_row_zipping_and_debt_classification() -> None:
    access = build_named_range_access(DEFAULT_FIXTURE["named_ranges"])
    categories, _ = parse_configuration_categories_and_groups(access)
    accounts = parse_configuration_accounts(access, categories)
    valuations = parse_net_worth_named_ranges(access, accounts)
    car_loan = next(valuation for valuation in valuations if valuation.raw_name == "Car Loan")
    assert car_loan.amount_minor == -1_000_000


def test_unused_broken_named_range_is_ignored() -> None:
    named_ranges = copy_named_ranges()
    named_ranges["UnknownBrokenRange"] = [["#REF!"]]
    bundle = parse_named_range_workbook(
        spreadsheet_id="fixture-default-sheet",
        spreadsheet_title="Copy of Finances 2.0",
        named_ranges=named_ranges,
        source_kind="fixture",
    )
    assert len(bundle.transactions) == 12


def test_trx_uuids_broken_range_is_ignored() -> None:
    named_ranges = copy_named_ranges()
    named_ranges["trx_Uuids"] = [["#REF!"]]
    bundle = parse_named_range_workbook(
        spreadsheet_id="fixture-default-sheet",
        spreadsheet_title="Copy of Finances 2.0",
        named_ranges=named_ranges,
        source_kind="fixture",
    )
    assert len(bundle.transactions) == 12


def test_required_named_range_import_fails_on_missing_named_range() -> None:
    named_ranges = dict(DEFAULT_FIXTURE["named_ranges"])
    named_ranges.pop("trx_Dates")
    with pytest.raises(ValueError, match="Missing required named ranges"):
        parse_named_range_workbook(
            spreadsheet_id="fixture-default-sheet",
            spreadsheet_title="Copy of Finances 2.0",
            named_ranges=named_ranges,
            source_kind="fixture",
        )


def test_required_named_range_import_fails_on_multicolumn_consumed_vector() -> None:
    named_ranges = copy_named_ranges()
    named_ranges["trx_Accounts"] = [["Checking", "Extra"]]
    with pytest.raises(ValueError, match="must be single-column"):
        parse_named_range_workbook(
            spreadsheet_id="fixture-default-sheet",
            spreadsheet_title="Copy of Finances 2.0",
            named_ranges=named_ranges,
            source_kind="fixture",
        )


def test_required_named_range_import_fails_on_length_incompatibility() -> None:
    named_ranges = copy_named_ranges()
    named_ranges["trx_Accounts"] = column(["Checking"])  # incompatible with transaction vectors
    with pytest.raises(ValueError, match="Meaningful transaction row 2 is missing required fields"):
        parse_named_range_workbook(
            spreadsheet_id="fixture-default-sheet",
            spreadsheet_title="Copy of Finances 2.0",
            named_ranges=named_ranges,
            source_kind="fixture",
        )


@pytest.mark.parametrize(
    ("field_name", "replacement"),
    [
        ("trx_Dates", ""),
        ("trx_Accounts", ""),
        ("trx_Statuses", ""),
    ],
)
def test_amount_bearing_transaction_rows_still_require_core_fields(
    field_name: str, replacement: str
) -> None:
    named_ranges = copy_named_ranges()
    named_ranges[field_name][0] = [replacement]

    with pytest.raises(ValueError, match="Meaningful transaction row 1 is missing required fields"):
        parse_named_range_workbook(
            spreadsheet_id="fixture-default-sheet",
            spreadsheet_title="Copy of Finances 2.0",
            named_ranges=named_ranges,
            source_kind="fixture",
        )


def test_first_amount_bearing_transaction_without_date_still_fails() -> None:
    named_ranges = copy_named_ranges()
    named_ranges["trx_Dates"][0] = [""]

    with pytest.raises(ValueError, match="Meaningful transaction row 1 is missing required fields"):
        parse_named_range_workbook(
            spreadsheet_id="fixture-default-sheet",
            spreadsheet_title="Copy of Finances 2.0",
            named_ranges=named_ranges,
            source_kind="fixture",
        )


def test_negative_allocation_amount_still_fails() -> None:
    named_ranges = copy_named_ranges()
    named_ranges["cts_Amounts"][0] = ["-$1.00"]

    with pytest.raises(ValueError, match="Allocation row 1 must contain a positive amount"):
        parse_named_range_workbook(
            spreadsheet_id="fixture-default-sheet",
            spreadsheet_title="Copy of Finances 2.0",
            named_ranges=named_ranges,
            source_kind="fixture",
        )


def test_meaningful_transaction_row_with_both_inflow_and_outflow_fails() -> None:
    named_ranges = copy_named_ranges()
    named_ranges["trx_Outflows"][0] = ["$10.00"]
    with pytest.raises(ValueError, match="both inflow and outflow"):
        parse_named_range_workbook(
            spreadsheet_id="fixture-default-sheet",
            spreadsheet_title="Copy of Finances 2.0",
            named_ranges=named_ranges,
            source_kind="fixture",
        )


def test_fixture_bundle_counts() -> None:
    bundle = fixture_bundle()
    assert len(bundle.accounts) == 3
    assert len(bundle.groups) == 3
    assert len(bundle.categories) == 4
    assert len(bundle.transactions) == 12
    assert len(bundle.allocations) == 8
    assert len(bundle.valuations) == 5


def test_contract_declares_three_shape_model() -> None:
    assert set(NamedRangeShape) == {
        NamedRangeShape.COLUMN_VECTOR,
        NamedRangeShape.TABLE_BLOCK,
        NamedRangeShape.SCALAR_OR_LABEL,
    }
    assert {entry.shape for entry in NAMED_RANGE_CONTRACT} == {
        NamedRangeShape.COLUMN_VECTOR,
        NamedRangeShape.TABLE_BLOCK,
        NamedRangeShape.SCALAR_OR_LABEL,
    }
    assert "config.category_group_names" not in CONTRACT_BY_LOGICAL_NAME
