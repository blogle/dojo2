"""Pure minor-unit investment position calculations."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PositionMetrics:
    value_minor: int
    cost_basis_minor: int
    unrealized_gain_minor: int


def position_amount_minor(quantity_micros: int, per_unit_minor: int) -> int:
    return (quantity_micros * per_unit_minor + 500_000) // 1_000_000


def position_metrics(
    *,
    quantity_micros: int,
    price_minor: int,
    average_basis_minor: int,
) -> PositionMetrics:
    value_minor = position_amount_minor(quantity_micros, price_minor)
    cost_basis_minor = position_amount_minor(quantity_micros, average_basis_minor)
    return PositionMetrics(
        value_minor=value_minor,
        cost_basis_minor=cost_basis_minor,
        unrealized_gain_minor=value_minor - cost_basis_minor,
    )
