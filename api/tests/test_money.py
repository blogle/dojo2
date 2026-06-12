from __future__ import annotations

import pytest

from dojo.money import format_money_minor, parse_money_value, parse_signed_amount


def test_parse_money_value() -> None:
    assert parse_money_value("$1,300.50") == 130050
    assert parse_money_value("-$15.00") == -1500
    assert parse_money_value("") is None


def test_parse_signed_amount() -> None:
    assert parse_signed_amount("$12.34", "") == 1234
    assert parse_signed_amount("", "$12.34") == -1234


def test_parse_signed_amount_rejects_double_entry() -> None:
    with pytest.raises(ValueError):
        parse_signed_amount("$1.00", "$1.00")


def test_format_money_minor() -> None:
    assert format_money_minor(1234) == "$12.34"
    assert format_money_minor(-1234) == "-$12.34"
