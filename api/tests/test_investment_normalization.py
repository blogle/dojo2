from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest
from pydantic import ValidationError

from dojo.api.models import InvestmentPositionPayload
from dojo.investment import PositionMetrics, position_metrics, total_cost_basis_minor


def _investment_account(service, name: str) -> str:
    return service.create_account({"name": name, "account_class": "INVESTMENT"})["account_id"]


def _position_payload(**changes):
    return {
        "effective_date": date(2026, 1, 1),
        "ticker": "XYZ",
        "quantity_micros": 1_000_000,
        "total_cost_basis_minor": 1234,
    } | changes


def test_average_cost_derivation_uses_half_even_ties() -> None:
    assert total_cost_basis_minor(500_000, 5) == 2
    assert total_cost_basis_minor(500_000, 7) == 4


def test_position_payload_preserves_direct_total_basis() -> None:
    payload = InvestmentPositionPayload(
        effective_date=date(2026, 1, 1),
        ticker="vti",
        quantity_micros=2_500_000,
        total_cost_basis_minor=20_000,
    )

    assert payload.model_dump()["total_cost_basis_minor"] == 20_000
    assert payload.ticker == "VTI"


def test_position_payload_accepts_average_basis_and_matching_direct_basis() -> None:
    average_only = InvestmentPositionPayload(
        effective_date=date(2026, 1, 1),
        ticker="VTI",
        quantity_micros=500_000,
        average_cost_per_share_minor=5,
    )
    matching = InvestmentPositionPayload(
        effective_date=date(2026, 1, 1),
        ticker="VTI",
        quantity_micros=500_000,
        average_cost_per_share_minor=5,
        total_cost_basis_minor=2,
    )

    assert average_only.average_cost_per_share_minor == 5
    assert matching.total_cost_basis_minor == 2


def test_position_payload_rejects_conflicting_or_missing_basis() -> None:
    common = {
        "effective_date": date(2026, 1, 1),
        "ticker": "VTI",
        "quantity_micros": 500_000,
    }
    with pytest.raises(ValidationError, match="conflict"):
        InvestmentPositionPayload(
            **common,
            average_cost_per_share_minor=5,
            total_cost_basis_minor=3,
        )
    with pytest.raises(ValidationError, match="total_cost_basis_minor"):
        InvestmentPositionPayload(**common)


def test_position_payload_requires_quantity() -> None:
    with pytest.raises(ValidationError, match="quantity_micros"):
        InvestmentPositionPayload(
            effective_date=date(2026, 1, 1),
            ticker="VTI",
            total_cost_basis_minor=100,
        )


def test_position_payload_accepts_no_symbol_when_instrument_id_exists() -> None:
    payload = InvestmentPositionPayload(
        effective_date=date(2026, 1, 1),
        instrument_id=uuid4(),
        quantity_micros=0,
        total_cost_basis_minor=0,
    )

    assert payload.symbol is None
    assert payload.ticker is None


def test_position_payload_rejects_blank_symbol_without_instrument_id() -> None:
    with pytest.raises(ValidationError, match="nonblank"):
        InvestmentPositionPayload(
            effective_date=date(2026, 1, 1),
            ticker="  ",
            quantity_micros=1,
            total_cost_basis_minor=1,
        )


def test_position_metrics_uses_canonical_total_basis_independent_of_price() -> None:
    metrics = position_metrics(
        quantity_micros=1_000_000,
        price_minor=20_000,
        total_cost_basis_minor=12_345,
    )

    assert metrics == PositionMetrics(
        value_minor=20_000,
        cost_basis_minor=12_345,
        unrealized_gain_minor=7_655,
    )


def test_instrument_without_symbol_persists_and_can_be_held(service) -> None:
    instrument = service.create_investment_instrument(
        {"symbol": None, "name": "Private fund", "is_cash_equivalent": False}
    )
    account_id = _investment_account(service, "Fund account")
    service.create_investment_position(
        account_id,
        _position_payload(instrument_id=instrument["instrument_id"], ticker=None),
    )

    assert instrument["symbol"] is None
    assert instrument in service.list_investment_instruments()
    assert service.list_investment_positions(account_id)[0]["instrument_id"] == instrument[
        "instrument_id"
    ]


def test_explicit_duplicate_symbol_create_reuses_global_instrument(service) -> None:
    first = service.create_investment_instrument({"symbol": "xyz"})
    second = service.create_investment_instrument({"symbol": "XYZ"})

    assert first["instrument_id"] == second["instrument_id"]
    assert len([item for item in service.list_investment_instruments() if item["symbol"] == "XYZ"]) == 1


def test_explicit_instrument_and_legacy_ticker_are_shared_across_accounts(service) -> None:
    instrument = service.create_investment_instrument({"symbol": "SHARED"})
    account_a = _investment_account(service, "Account A")
    account_b = _investment_account(service, "Account B")
    service.create_investment_position(
        account_a, _position_payload(instrument_id=instrument["instrument_id"], ticker=None)
    )
    service.create_investment_position(account_b, _position_payload(ticker="shared"))

    positions_a = service.list_investment_positions(account_a)
    positions_b = service.list_investment_positions(account_b)
    assert positions_a[0]["instrument_id"] == positions_b[0]["instrument_id"]
    assert positions_a[0]["instrument_id"] == instrument["instrument_id"]


def test_position_creation_persists_direct_and_derived_total_basis(service) -> None:
    account_id = _investment_account(service, "Basis account")
    direct_result = service.create_investment_position(account_id, _position_payload())
    derived_result = service.create_investment_position(
        account_id,
        _position_payload(
            ticker="HALF",
            quantity_micros=500_000,
            total_cost_basis_minor=None,
            average_cost_per_share_minor=7,
        ),
    )
    direct = service.db.fetch_one(
        "SELECT * FROM current_investment_positions WHERE position_id = ?",
        (direct_result["position_id"],),
    )
    derived = service.db.fetch_one(
        "SELECT * FROM current_investment_positions WHERE position_id = ?",
        (derived_result["position_id"],),
    )
    columns = {
        row["column_name"]
        for row in service.db.fetch_all(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'investment_positions'"
        )
    }

    assert direct["total_cost_basis_minor"] == 1234
    assert derived["total_cost_basis_minor"] == 4
    assert "average_basis_minor" not in columns
    assert "instrument_id" in columns
    assert service.list_investment_positions(account_id)[0]["instrument_id"]
    assert service.list_investment_positions(account_id)[0]["total_cost_basis_minor"] in {1234, 4}
    basis_column = service.db.fetch_one(
        "SELECT is_nullable FROM information_schema.columns "
        "WHERE table_name = 'investment_positions' AND column_name = 'total_cost_basis_minor'"
    )
    assert basis_column == {"is_nullable": "NO"}


def test_position_correction_requires_basis_when_quantity_changes(service) -> None:
    account_id = _investment_account(service, "Correction account")
    created = service.create_investment_position(account_id, _position_payload())
    position_id = created["position_id"]
    with pytest.raises(ValueError, match="requires a resulting cost basis"):
        service.correct_investment_position(
            account_id, position_id, {"quantity_micros": 2_000_000}
        )

    assert service.db.fetch_one(
        "SELECT COUNT(*) AS count FROM investment_positions WHERE position_id = ?",
        (position_id,),
    )["count"] == 1
    assert service.list_investment_positions(account_id)[0]["quantity_micros"] == 1_000_000


def test_position_correction_with_direct_basis_preserves_scd_identity(service) -> None:
    account_id = _investment_account(service, "Direct correction account")
    created = service.create_investment_position(account_id, _position_payload())
    position_id = created["position_id"]
    service.correct_investment_position(
        account_id,
        position_id,
        {"quantity_micros": 2_000_000, "total_cost_basis_minor": 2500},
    )
    history = service.db.fetch_all(
        "SELECT position_id, quantity_micros, total_cost_basis_minor, valid_to "
        "FROM investment_positions WHERE position_id = ? ORDER BY valid_from",
        (position_id,),
    )

    assert len(history) == 2
    assert {row["position_id"] for row in history} == {position_id}
    assert [row["quantity_micros"] for row in history] == [1_000_000, 2_000_000]
    assert history[-1]["total_cost_basis_minor"] == 2500


def test_position_correction_with_average_input_rounds_half_even(service) -> None:
    account_id = _investment_account(service, "Average correction account")
    created = service.create_investment_position(account_id, _position_payload())
    service.correct_investment_position(
        account_id,
        created["position_id"],
        {"quantity_micros": 500_000, "average_cost_per_share_minor": 7},
    )
    current = service.db.fetch_one(
        "SELECT quantity_micros, total_cost_basis_minor FROM current_investment_positions "
        "WHERE position_id = ?",
        (created["position_id"],),
    )

    assert current == {"quantity_micros": 500_000, "total_cost_basis_minor": 4}


def test_quantity_preserving_correction_without_basis_retains_basis(service) -> None:
    account_id = _investment_account(service, "Preserving correction account")
    created = service.create_investment_position(account_id, _position_payload())
    service.correct_investment_position(account_id, created["position_id"], {})
    history = service.db.fetch_all(
        "SELECT total_cost_basis_minor FROM investment_positions WHERE position_id = ?",
        (created["position_id"],),
    )

    assert len(history) == 2
    assert [row["total_cost_basis_minor"] for row in history] == [1234, 1234]
