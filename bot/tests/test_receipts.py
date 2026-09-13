from decimal import Decimal

from obshak_bot.receipts import parse_fiscal_qr
from obshak_bot.services import AuthService, ReceiptService, TelegramUser
from obshak_bot.storage import Database, UserSessionRepository
from tests.fake_backend import FakeBackend

ARTEM = TelegramUser(id=42, name="Артём")


def test_parse_fiscal_qr_plain_and_url() -> None:
    assert parse_fiscal_qr("t=20240115T1430&s=1234.56&fn=1&i=2&fp=3&n=1") == Decimal("1234.56")
    assert parse_fiscal_qr(
        "https://lk.platformaofd.ru/web/noauth/cheque?fn=1&s=99,90&i=2"
    ) == Decimal("99.90")
    assert parse_fiscal_qr("t=20240115T1430&s=10&fn=1") == Decimal("10.00")


def test_parse_fiscal_qr_rejects_garbage() -> None:
    assert parse_fiscal_qr("") is None
    assert parse_fiscal_qr("just a shop name") is None
    assert parse_fiscal_qr("https://example.com/foo") is None
    assert parse_fiscal_qr("s=-5") is None


async def test_recognize_prefers_fiscal_qr(db: Database) -> None:
    backend = FakeBackend()
    api = backend.client()
    service = ReceiptService(
        api,
        AuthService(api, UserSessionRepository(db)),
        decode_qr=lambda _: "t=20240115T1430&s=250.00&fn=1&i=2&fp=3&n=1",
    )

    result = await service.recognize(ARTEM, b"fake-image")

    assert result is not None
    assert result.source == "qr" and result.amount == Decimal("250.00")
    assert not any(c.startswith("POST /api/expenses/receipt") for c in backend.calls)


async def test_recognize_falls_back_to_backend_stub(db: Database) -> None:
    backend = FakeBackend()
    api = backend.client()
    service = ReceiptService(
        api, AuthService(api, UserSessionRepository(db)), decode_qr=lambda _: None
    )

    result = await service.recognize(ARTEM, b"fake-image")

    assert result is not None
    assert result.source == "backend" and result.amount == Decimal("1234.56")


async def test_recognize_none_when_qr_useless_and_backend_errors(db: Database) -> None:
    backend = FakeBackend()
    backend.receipt_broken = True
    api = backend.client()
    service = ReceiptService(
        api, AuthService(api, UserSessionRepository(db)), decode_qr=lambda _: "not-a-receipt"
    )

    assert await service.recognize(ARTEM, b"x") is None
