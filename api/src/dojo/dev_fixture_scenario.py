from __future__ import annotations

from calendar import monthrange
from datetime import date

from dojo.importer import NamedRangeMatrix

GROUPS: dict[str, tuple[str, ...]] = {
    "Home": ("Rent", "Electricity", "Water", "Internet", "Home Supplies"),
    "Food": ("Groceries", "Restaurants", "Coffee", "Work Lunches"),
    "Getting Around": ("Fuel", "Transit", "Auto Care", "Rideshare", "Auto Loan Payment"),
    "Health": ("Medical", "Pharmacy", "Fitness"),
    "Family": ("Childcare", "School", "Pet Care"),
    "Plans": ("Phone", "Streaming", "Cloud Storage", "Insurance"),
    "Saving": ("Emergency Reserve", "Annual Travel", "Gifts", "Home Project"),
    "Personal": ("Clothing", "Hobbies", "Books", "Personal Care"),
    "Credit Card Payments": ("Cedar Card Payment",),
}

ACCOUNTS = (
    "Maple Checking",
    "Maple Savings",
    "Everyday Wallet",
    "Cedar Card",
    "Juniper Cash",
)
MERCHANTS = {
    "Rent": ("Juniper Property", 145_000),
    "Electricity": ("Bright Current", 11_500),
    "Water": ("Clearwater Utility", 4_800),
    "Internet": ("Orbit Fiber", 6_500),
    "Home Supplies": ("Corner Hardware", 3_800),
    "Groceries": ("Market Basket", 18_000),
    "Restaurants": ("Lantern Kitchen", 7_200),
    "Coffee": ("Drift Coffee", 1_800),
    "Work Lunches": ("Station Cafe", 2_600),
    "Fuel": ("Northside Fuel", 6_500),
    "Transit": ("Metro Pass", 4_200),
    "Auto Care": ("Pine Garage", 3_000),
    "Rideshare": ("City Ride", 1_600),
    "Auto Loan Payment": ("Cedar Auto Loan", 0),
    "Medical": ("Harbor Clinic", 2_500),
    "Pharmacy": ("Clover Pharmacy", 1_200),
    "Fitness": ("Common Ground Gym", 3_900),
    "Childcare": ("Little Harbor Center", 42_000),
    "School": ("Fieldstone School", 5_000),
    "Pet Care": ("Willow Pet Clinic", 2_200),
    "Phone": ("Signal Mobile", 5_400),
    "Streaming": ("Mosaic Video", 1_600),
    "Cloud Storage": ("Northstar Cloud", 900),
    "Insurance": ("Evergreen Mutual", 12_500),
    "Emergency Reserve": ("Reserve transfer", 0),
    "Annual Travel": ("Travel savings", 0),
    "Gifts": ("Gift savings", 0),
    "Home Project": ("Project savings", 0),
    "Clothing": ("Thread & Pine", 4_000),
    "Hobbies": ("Workshop Supply", 3_500),
    "Books": ("Papertrail Books", 1_400),
    "Personal Care": ("Daylight Studio", 2_400),
}
MONTHLY_PLANS = {
    "Groceries": 80_000,
    "Restaurants": 12_000,
    "Coffee": 7_500,
    "Work Lunches": 10_000,
    "Fuel": 24_000,
    "Transit": 8_000,
    "Auto Care": 10_000,
    "Rideshare": 7_000,
    "Medical": 8_000,
    "Pharmacy": 5_000,
    "Fitness": 4_000,
    "Childcare": 42_000,
    "School": 5_000,
    "Pet Care": 4_000,
    "Phone": 6_000,
    "Streaming": 2_000,
    "Cloud Storage": 1_500,
    "Insurance": 13_000,
    "Clothing": 8_000,
    "Hobbies": 7_000,
    "Books": 4_000,
    "Personal Care": 5_000,
}


def development_named_ranges() -> dict[str, NamedRangeMatrix]:
    dates: list[str] = []
    outflows: list[str] = []
    inflows: list[str] = []
    categories: list[str] = []
    accounts: list[str] = []
    memos: list[str] = []
    statuses: list[str] = []

    def transaction(
        day: date,
        account: str,
        amount_minor: int,
        category: str,
        memo: str,
        *,
        pending: bool = False,
    ) -> None:
        dates.append(day.isoformat())
        outflows.append(_money(-amount_minor) if amount_minor < 0 else "")
        inflows.append(_money(amount_minor) if amount_minor > 0 else "")
        categories.append(category)
        accounts.append(account)
        memos.append(memo)
        statuses.append("PEND" if pending else "APP")

    transaction(date(2026, 1, 1), ACCOUNTS[0], 820_000, "SB", "Opening checking balance")
    transaction(date(2026, 1, 1), ACCOUNTS[1], 2_400_000, "SB", "Opening reserve balance")
    transaction(date(2026, 1, 1), ACCOUNTS[2], 18_000, "SB", "Opening wallet balance")
    transaction(date(2026, 1, 1), ACCOUNTS[3], -62_000, "SB", "Opening card balance")
    transaction(date(2026, 1, 1), ACCOUNTS[4], 32_000, "SB", "Opening cash account balance")

    allocation_dates: list[str] = []
    allocation_amounts: list[str] = []
    allocation_from: list[str] = []
    allocation_to: list[str] = []
    allocation_memos: list[str] = []
    for month in range(1, 7):
        last_day = monthrange(2026, month)[1]
        transaction(date(2026, month, 1), ACCOUNTS[0], 315_000, "ATB", "Juniper Works payroll")
        transaction(date(2026, month, 15), ACCOUNTS[0], 315_000, "ATB", "Juniper Works payroll")
        transaction(date(2026, month, 20), ACCOUNTS[0], 42_000, "ATB", "Studio North contract")

        # Several goals remain unfunded to demonstrate an upcoming shortfall.
        for category_name in MERCHANTS:
            if category_name == "Cedar Card Payment":
                continue
            amount = MONTHLY_PLANS.get(category_name, MERCHANTS[category_name][1])
            amount += 1_000 if amount else 0
            if amount:
                allocation_dates.append(date(2026, month, 2).isoformat())
                allocation_amounts.append(_money(amount))
                allocation_from.append("ATB")
                allocation_to.append(category_name)
                allocation_memos.append(f"{category_name} monthly plan")

        for category_index, category_name in enumerate(MERCHANTS):
            merchant, amount = MERCHANTS[category_name]
            if not amount:
                continue
            # A deterministic mix gives each category activity without making
            # low-frequency annual and project categories look artificially busy.
            if category_index >= 23 and month not in {2, 4, 6}:
                continue
            day = min(3 + (category_index * 3) % 24, last_day)
            use_card = category_index % 3 == 1
            account = ACCOUNTS[3] if use_card else ACCOUNTS[0]
            pending = month == 6 and category_name in {"Groceries", "Fuel"}
            actual_amount = amount + ((month + category_index) % 4) * 350
            if category_name == "Rent":
                actual_amount = amount
            transaction(
                date(2026, month, day),
                account,
                -actual_amount,
                category_name,
                f"{merchant} purchase",
                pending=pending,
            )

        for occurrence in range(1, 5):
            transaction(
                date(2026, month, 4 + occurrence * 5),
                ACCOUNTS[0],
                -(18_000 + occurrence * 175),
                "Groceries",
                f"Market Basket weekly shop {occurrence}",
            )
        for occurrence in range(1, 3):
            transaction(
                date(2026, month, 8 + occurrence * 9),
                ACCOUNTS[3],
                -(4_600 + occurrence * 225),
                "Restaurants",
                f"Lantern Kitchen meal {occurrence}",
            )

        if month == 3:
            transaction(
                date(2026, month, 12), ACCOUNTS[0], 2_400, "Groceries", "Market Basket refund"
            )
            transaction(date(2026, month, 18), ACCOUNTS[0], 6_800, "", "Shared cabin reimbursement")
        if month == 4:
            transaction(date(2026, month, 10), ACCOUNTS[0], -9_500, "XFER", "Move to savings")
            transaction(date(2026, month, 10), ACCOUNTS[1], 9_500, "XFER", "Move from checking")
        if month == 6:
            transaction(date(2026, month, 25), ACCOUNTS[0], -25_000, "XFER", "Cedar card payment")
            transaction(date(2026, month, 25), ACCOUNTS[3], 25_000, "XFER", "Payment received")
            transaction(
                date(2026, month, 26),
                ACCOUNTS[0],
                -3_200,
                "",
                "Uncategorized market purchase",
                pending=True,
            )

    category_names = [name for names in GROUPS.values() for name in names]
    category_groups = [group for group, names in GROUPS.items() for _ in names]
    targets = [
        24_000 if name == "Auto Loan Payment" else MERCHANTS.get(name, ("", 0))[1] or 8_000
        for name in category_names
    ]
    goals = ["Monthly" if i % 4 != 0 else "" for i, _ in enumerate(category_names)]
    net_worth_dates: list[str] = []
    net_worth_amounts: list[str] = []
    net_worth_categories: list[str] = []
    net_worth_notes: list[str] = []

    config_rows: list[list[str]] = []
    for group, names in GROUPS.items():
        config_rows.append(["GROUP", group, "", ""])
        for name in names:
            config_rows.append(
                [
                    "DEBT" if name == "Cedar Card Payment" else "CAT",
                    name,
                    "",
                    "",
                ]
            )

    def column(values: list[str]) -> list[list[str]]:
        return [[value] for value in values]

    return {
        "trx_Dates": column(dates),
        "trx_Outflows": column(outflows),
        "trx_Inflows": column(inflows),
        "trx_Categories": column(categories),
        "trx_Accounts": column(accounts),
        "trx_Memos": column(memos),
        "trx_Statuses": column(statuses),
        "cts_Dates": column(allocation_dates),
        "cts_Amounts": column(allocation_amounts),
        "cts_FromCategories": column(allocation_from),
        "cts_ToCategories": column(allocation_to),
        "cts_Memos": column(allocation_memos),
        "ntw_Dates": column(net_worth_dates),
        "ntw_Amounts": column(net_worth_amounts),
        "ntw_Categories": column(net_worth_categories),
        "ntw_Notes": column(net_worth_notes),
        "cfg_Accounts": column([*ACCOUNTS[:3], ACCOUNTS[4]]),
        "cfg_Cards": column([ACCOUNTS[3]]),
        "CreditCardAccounts": column([ACCOUNTS[3]]),
        "UserDefAccounts": column(list(ACCOUNTS)),
        "UserDefCategories": column(category_names),
        "UserDefCategoryGroupNames": column(category_groups),
        "UserDefAmounts": column([_money(value) for value in targets]),
        "UserDefGoals": column(goals),
        "UserDefLinkedAccounts": column(
            [ACCOUNTS[3] if name == "Cedar Card Payment" else "" for name in category_names]
        ),
        "NetWorthCategories": column(["Juniper Home", "Cedar Auto Loan", "Harbor Education Fund"]),
        "NetWorthDebts": column(["Cedar Auto Loan"]),
        "r_ConfigurationData": config_rows,
        "v_AtoB": [["ATB"]],
        "v_AccountTransfer": [["XFER"]],
        "v_BalanceAdjustment": [["BALADJ"]],
        "v_StartingBalance": [["SB"]],
        "v_ApprovedSymbol": [["APP"]],
        "v_PendingSymbol": [["PEND"]],
        "v_BreakSymbol": [["BREAK"]],
        "v_CategoryGroupSymbol": [["GROUP"]],
        "v_ReportableCategorySymbol": [["CAT"]],
        "v_NonReportableCategorySymbol": [["NRCAT"]],
        "v_DebtAccountSymbol": [["DEBT"]],
        "v_GoalSymbol": [["GOAL"]],
    }


def _money(amount_minor: int) -> str:
    return f"${amount_minor // 100:,}.{amount_minor % 100:02d}"
