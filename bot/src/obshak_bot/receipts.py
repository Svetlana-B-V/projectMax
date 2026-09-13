"""Фискальный QR российского чека (54-ФЗ): t=…&s=СУММА&fn=…"""

from decimal import Decimal
from urllib.parse import parse_qs, urlparse

from obshak_bot.money import parse_amount


def parse_fiscal_qr(payload: str) -> Decimal | None:
    """Достать сумму из текста QR. None — если это не фискальный чек."""
    query = _query_string(payload.strip())
    if not query:
        return None
    params = parse_qs(query.replace(";", "&"), keep_blank_values=False)
    raw = (params.get("s") or params.get("sum") or [None])[0]
    if raw is None:
        return None
    return parse_amount(raw.replace(" ", ""))


def decode_qr_from_bytes(image: bytes) -> str | None:
    """Найти первый QR на фото. None — нет QR или нет OpenCV."""
    try:
        import cv2
        import numpy as np
    except ImportError:
        return None
    arr = np.frombuffer(image, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return None
    payload, *_ = cv2.QRCodeDetector().detectAndDecode(img)
    return payload or None


def _query_string(payload: str) -> str:
    if "://" in payload:
        parsed = urlparse(payload)
        return parsed.query or parsed.fragment
    if "?" in payload:
        return payload.split("?", 1)[1]
    if "=" in payload:
        return payload
    return ""
