from __future__ import annotations


def column(values: list[str]) -> list[list[str]]:
    return [[value] for value in values]


def scalar(value: str) -> list[list[str]]:
    return [[value]]


DEFAULT_FIXTURE = {
    "spreadsheet_id": "fixture-default-sheet",
    "spreadsheet_title": "Copy of Finances 2.0",
    "named_ranges": {
        "trx_Dates": column(
            [
                "2026-01-01",
                "2026-01-01",
                "2026-01-05",
                "2026-01-06",
                "2026-01-07",
                "2026-01-08",
                "2026-01-09",
                "2026-01-10",
                "",
                "2026-01-11",
                "2026-01-11",
                "2026-02-01",
                "2026-02-03",
                "",
                "",
            ]
        ),
        "trx_Outflows": column(
            [
                "",
                "$200.00",
                "",
                "$50.00",
                "$120.00",
                "",
                "",
                "$40.00",
                "",
                "$100.00",
                "",
                "",
                "$70.00",
            ]
        ),
        "trx_Inflows": column(
            [
                "$1,000.00",
                "",
                "$3,000.00",
                "",
                "",
                "$20.00",
                "$150.00",
                "",
                "",
                "",
                "$100.00",
                "$1,000.00",
                "",
                "",
                "",
            ]
        ),
        "trx_Categories": column(
            [
                "SB",
                "SB",
                "ATB",
                "Grocery",
                "Grocery",
                "Grocery",
                "SB",
                "Secret Stash",
                "",
                "XFER",
                "XFER",
                "ATB",
                "Utilities",
                "",
                "",
            ]
        ),
        "trx_Accounts": column(
            [
                "Checking",
                "Reserve Card",
                "Checking",
                "Checking",
                "Reserve Card",
                "Reserve Card",
                "Wallet",
                "Checking",
                "",
                "Checking",
                "Reserve Card",
                "Checking",
                "Checking",
                "",
                "",
            ]
        ),
        "trx_Memos": column(
            [
                "Initial checking",
                "Starting card debt",
                "Paycheck",
                "Groceries",
                "Card groceries",
                "Refund",
                "Cash on hand",
                "Hidden category spend",
                "",
                "Pay card",
                "Pay card",
                "Side work",
                "Electric bill",
                "",
                "",
            ]
        ),
        "trx_Statuses": column(
            [
                "APP",
                "APP",
                "APP",
                "APP",
                "APP",
                "APP",
                "APP",
                "PEND",
                "BREAK",
                "APP",
                "APP",
                "APP",
                "APP",
                "",
                "",
            ]
        ),
        "cts_Dates": column(
            [
                "2026-01-05",
                "2026-01-05",
                "2026-01-05",
                "2026-01-05",
                "2026-01-12",
                "2026-01-15",
                "2026-02-01",
                "2026-02-01",
                "",
            ]
        ),
        "cts_Amounts": column(
            [
                "$300.00",
                "$200.00",
                "$100.00",
                "$150.00",
                "$50.00",
                "$20.00",
                "$100.00",
                "$80.00",
            ]
        ),
        "cts_FromCategories": column(
            [
                "ATB",
                "ATB",
                "ATB",
                "ATB",
                "Grocery",
                "Utilities",
                "ATB",
                "ATB",
            ]
        ),
        "cts_ToCategories": column(
            [
                "Grocery",
                "Utilities",
                "Secret Stash",
                "Reserve Card Payment",
                "Utilities",
                "ATB",
                "Grocery",
                "Utilities",
                "",
            ]
        ),
        "cts_Memos": column(
            [
                "Fund grocery",
                "Fund utilities",
                "Fund hidden",
                "Fund card debt",
                "Move grocery to utilities",
                "Return extra",
                "February grocery",
                "February utilities",
                "",
            ]
        ),
        "ntw_Dates": column(
            [
                "2026-02-01",
                "2026-02-01",
                "2026-02-01",
                "2026-02-01",
                "2026-02-01",
                "",
            ]
        ),
        "ntw_Amounts": column(
            [
                "$4,740.00",
                "$150.00",
                "-$200.00",
                "$500,000.00",
                "-$10,000.00",
                "",
            ]
        ),
        "ntw_Categories": column(
            [
                "Checking",
                "Wallet",
                "Reserve Card",
                "House Value",
                "Car Loan",
                "",
            ]
        ),
        "ntw_Notes": column(
            [
                "Ignored budget account",
                "Ignored hidden budget account",
                "Ignored budget liability",
                "Home estimate",
                "Loan balance",
                "",
            ]
        ),
        "cfg_Accounts": column(["Checking", "Wallet"]),
        "cfg_Cards": column(["Reserve Card"]),
        "CreditCardAccounts": column(["Reserve Card"]),
        "UserDefAccounts": column(["Checking", "Wallet", "Reserve Card"]),
        "HiddenAccounts": column(["Wallet"]),
        "UserDefCategories": column(
            ["Grocery", "Utilities", "Secret Stash", "Reserve Card Payment"]
        ),
        "UserDefCategoryGroupNames": column(["Living", "Bills", "Living", "Credit Card Payments"]),
        "UserDefAmounts": column(["$300.00", "$150.00", "$100.00", ""]),
        "UserDefGoals": column(["", "Monthly", "", ""]),
        "UserDefLinkedAccounts": column(["", "", "", "Reserve Card"]),
        "HiddenCategories": column(["Secret Stash"]),
        "NetWorthCategories": column(
            ["Checking", "Wallet", "Reserve Card", "House Value", "Car Loan"]
        ),
        "NetWorthAssets": column(["Checking", "Wallet", "House Value"]),
        "NetWorthDebts": column(["Reserve Card", "Car Loan"]),
        "r_ConfigurationData": [
            ["GROUP", "Living", "", ""],
            ["CAT", "Grocery", "$300.00", ""],
            ["NRCAT", "Secret Stash", "$100.00", ""],
            ["GROUP", "Bills", "", ""],
            ["CAT", "Utilities", "$150.00", "Monthly"],
            ["GROUP", "Credit Card Payments", "", ""],
            ["DEBT", "Reserve Card Payment", "", ""],
        ],
        "r_DashboardData": [["Metric", "Value"], ["ATB", "$4,040.00"]],
        "v_AtoB": scalar("ATB"),
        "v_AccountTransfer": scalar("XFER"),
        "v_BalanceAdjustment": scalar("BALADJ"),
        "v_StartingBalance": scalar("SB"),
        "v_ApprovedSymbol": scalar("APP"),
        "v_PendingSymbol": scalar("PEND"),
        "v_BreakSymbol": scalar("BREAK"),
        "v_CategoryGroupSymbol": scalar("GROUP"),
        "v_ReportableCategorySymbol": scalar("CAT"),
        "v_NonReportableCategorySymbol": scalar("NRCAT"),
        "v_DebtAccountSymbol": scalar("DEBT"),
        "v_GoalSymbol": scalar("GOAL"),
        "UnusedNamedRange": scalar("ignored"),
    },
    "expected": {
        "account_count": 5,
        "category_group_count": 3,
        "category_count": 4,
        "net_worth_valuation_rows": 5,
        "account_balances": {
            "Checking": {"actual": 474000, "pending": -4000, "cleared": 478000},
            "Wallet": {"actual": 15000, "pending": 0, "cleared": 15000},
            "Reserve Card": {"actual": -20000, "pending": 0, "cleared": -20000},
        },
        "atb_available_minor": 424000,
        "category_available": {
            "Grocery": 20000,
            "Utilities": 24000,
            "Secret Stash": 6000,
            "Reserve Card Payment": 15000,
        },
        "month_activity": {
            "2026-01": {
                "Grocery": -15000,
                "Utilities": 0,
                "Secret Stash": -4000,
                "Reserve Card Payment": 0,
            },
            "2026-02": {
                "Grocery": 0,
                "Utilities": -7000,
                "Secret Stash": 0,
                "Reserve Card Payment": 0,
            },
        },
        "month_budgeted": {
            "2026-01": {
                "Grocery": 25000,
                "Utilities": 23000,
                "Secret Stash": 10000,
                "Reserve Card Payment": 15000,
            },
            "2026-02": {
                "Grocery": 10000,
                "Utilities": 8000,
                "Secret Stash": 0,
                "Reserve Card Payment": 0,
            },
        },
        "starting_available": {
            "2026-01": {
                "Grocery": 0,
                "Utilities": 0,
                "Secret Stash": 0,
                "Reserve Card Payment": 0,
            },
            "2026-02": {
                "Grocery": 10000,
                "Utilities": 23000,
                "Secret Stash": 6000,
                "Reserve Card Payment": 15000,
            },
        },
        "native_net_worth_minor": 49469000,
    },
}
