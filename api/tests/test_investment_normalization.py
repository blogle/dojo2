from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest
from pydantic import ValidationError

from dojo.api.models import InvestmentPositionPayload
from dojo.investment import PositionMetrics, position_metrics, total_cost_basis_minor


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
