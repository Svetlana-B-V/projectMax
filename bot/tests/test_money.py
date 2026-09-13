from decimal import Decimal

import pytest

from obshak_bot.money import format_amount, parse_amount, split_equally


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("1250", Decimal("1250.00")),
        ("99,90", Decimal("99.90")),
        ("1 234.5", Decimal("1234.50")),
        ("500 ₽", Decimal("500.00")),
        ("0.01", Decimal("0.01")),
    ],
)
def test_parse_amount_accepts_common_formats(text: str, expected: Decimal) -> None:
    assert parse_amount(text) == expected


@pytest.mark.parametrize("text", ["", "abc", "0", "-5", "1.234", "99999999999", "1e3", "NaN"])
def test_parse_amount_rejects_garbage(text: str) -> None:
    assert parse_amount(text) is None


def test_format_amount_uses_russian_style() -> None:
    assert format_amount(Decimal("1234567.5")) == "1 234 567,50 ₽"
    assert format_amount(Decimal("7")) == "7,00 ₽"


def test_split_equally_keeps_every_kopeck() -> None:
    share, remainder = split_equally(Decimal("100"), 3)
    assert share == Decimal("33.33")
    assert remainder == Decimal("0.01")
    assert share * 3 + remainder == Decimal("100")

    share, remainder = split_equally(Decimal("90"), 3)
    assert (share, remainder) == (Decimal("30.00"), Decimal("0"))
