"""Деньги в рублях: разбор ввода, форматирование, деление без потери копеек."""

import re
from decimal import ROUND_DOWN, Decimal

KOPECK = Decimal("0.01")
MAX_AMOUNT = Decimal("10000000")  # верхняя граница ввода, чтобы не упереться в DECIMAL(10,2)
_AMOUNT_RE = re.compile(r"^\d+(?:[.,]\d{1,2})?$")


def parse_amount(text: str) -> Decimal | None:
    """«1 234,50», «1234.5», «500 ₽» → Decimal с копейками. None — если это не сумма."""
    cleaned = text.strip().rstrip("₽рРpP ").replace(" ", "").replace("\u00a0", "")
    if not _AMOUNT_RE.match(cleaned):
        return None
    value = Decimal(cleaned.replace(",", ".")).quantize(KOPECK)
    if value <= 0 or value > MAX_AMOUNT:
        return None
    return value


def format_amount(value: Decimal) -> str:
    """Decimal('1234.5') → «1 234,50 ₽»."""
    return f"{value:,.2f}".replace(",", " ").replace(".", ",") + " ₽"


def split_equally(total: Decimal, count: int) -> tuple[Decimal, Decimal]:
    """Поделить поровну, округляя вниз до копейки. Возвращает (доля, нераспределённый остаток)."""
    if count <= 0:
        raise ValueError("count must be positive")
    share = (total / count).quantize(KOPECK, rounding=ROUND_DOWN)
    return share, total - share * count
