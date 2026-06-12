from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation


def parse_money_value(raw: str | None) -> int | None:
    if raw is None:
        return None

    value = raw.strip()
    if not value:
        return None

    normalized = value.replace(",", "").replace("$", "").replace("(", "-").replace(")", "")
    try:
        amount = Decimal(normalized)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid money value: {raw}") from exc

    cents = (amount * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(cents)


def parse_signed_amount(inflow: str | None, outflow: str | None) -> int:
    inflow_minor = parse_money_value(inflow)
    outflow_minor = parse_money_value(outflow)

    if inflow_minor is not None and outflow_minor is not None:
        raise ValueError("Transaction row cannot have both inflow and outflow populated")

    if inflow_minor is None and outflow_minor is None:
        raise ValueError("Transaction row must have either inflow or outflow populated")

    if inflow_minor is not None:
        return inflow_minor
    assert outflow_minor is not None
    return -outflow_minor


def format_money_minor(amount_minor: int) -> str:
    sign = "-" if amount_minor < 0 else ""
    absolute = abs(amount_minor)
    dollars, cents = divmod(absolute, 100)
    return f"{sign}${dollars:,}.{cents:02d}"
