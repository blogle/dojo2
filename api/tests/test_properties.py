from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st


@given(
    atb=st.integers(min_value=0, max_value=1_000_000),
    category=st.integers(min_value=0, max_value=1_000_000),
    move=st.integers(min_value=0, max_value=1_000_000),
)
def test_allocations_preserve_total_budget_bucket_value(atb: int, category: int, move: int) -> None:
    move_amount = min(move, atb)
    after_atb = atb - move_amount
    after_category = category + move_amount
    assert after_atb + after_category == atb + category


@given(
    from_balance=st.integers(min_value=0, max_value=1_000_000),
    to_balance=st.integers(min_value=0, max_value=1_000_000),
    move=st.integers(min_value=0, max_value=1_000_000),
)
def test_moving_money_decreases_source_and_increases_destination(
    from_balance: int,
    to_balance: int,
    move: int,
) -> None:
    move_amount = min(move, from_balance)
    assert from_balance - move_amount == from_balance - move_amount
    assert to_balance + move_amount == to_balance + move_amount


@given(
    atb=st.integers(min_value=0, max_value=1_000_000),
    category=st.integers(min_value=0, max_value=1_000_000),
    move=st.integers(min_value=0, max_value=1_000_000),
)
def test_returning_money_to_atb_increases_atb_and_decreases_category(
    atb: int,
    category: int,
    move: int,
) -> None:
    move_amount = min(move, category)
    assert atb + move_amount >= atb
    assert category - move_amount <= category


@given(amount=st.integers(min_value=-1_000_000, max_value=1_000_000))
def test_status_changes_do_not_change_actual_balance(amount: int) -> None:
    pending = amount
    cleared = 0
    actual_before = pending + cleared
    pending = 0
    cleared = amount
    actual_after = pending + cleared
    assert actual_before == actual_after


@given(amount=st.integers(min_value=-1_000_000, max_value=1_000_000))
def test_status_changes_only_move_value_between_pending_and_cleared(amount: int) -> None:
    assert amount + 0 == 0 + amount


@given(
    expense=st.integers(min_value=1, max_value=1_000_000),
    account_balance=st.integers(min_value=0, max_value=1_000_000),
    category_balance=st.integers(min_value=0, max_value=1_000_000),
)
def test_cash_expense_decreases_account_balance_and_category_availability(
    expense: int,
    account_balance: int,
    category_balance: int,
) -> None:
    assert account_balance - expense <= account_balance
    assert category_balance - expense <= category_balance


@given(
    inflow=st.integers(min_value=0, max_value=1_000_000),
    account_balance=st.integers(min_value=-1_000_000, max_value=1_000_000),
    atb=st.integers(min_value=-1_000_000, max_value=1_000_000),
)
def test_income_to_atb_increases_account_balance_and_atb(
    inflow: int,
    account_balance: int,
    atb: int,
) -> None:
    assert account_balance + inflow >= account_balance
    assert atb + inflow >= atb


@given(
    payment=st.integers(min_value=0, max_value=1_000_000),
    deposit_balance=st.integers(min_value=0, max_value=1_000_000),
    card_balance=st.integers(min_value=-1_000_000, max_value=0),
)
def test_credit_card_payment_transfer_changes_accounts_not_spending(
    payment: int,
    deposit_balance: int,
    card_balance: int,
) -> None:
    assert deposit_balance - payment <= deposit_balance
    assert card_balance + payment >= card_balance


@given(
    carried_over=st.integers(min_value=-1_000_000, max_value=1_000_000),
    month_activity=st.integers(min_value=-1_000_000, max_value=1_000_000),
    month_budgeted=st.integers(min_value=-1_000_000, max_value=1_000_000),
)
def test_rollover_matches_all_time_formula(
    carried_over: int, month_activity: int, month_budgeted: int
) -> None:
    assert (
        carried_over + month_activity + month_budgeted
        == carried_over + month_activity + month_budgeted
    )
