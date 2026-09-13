import logging
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from obshak_bot.api import ApiError, ApiUnavailable, ObshakApiClient
from obshak_bot.receipts import decode_qr_from_bytes, parse_fiscal_qr
from obshak_bot.services.auth import AuthService, TelegramUser

log = logging.getLogger(__name__)

DecodeQr = Callable[[bytes], str | None]


@dataclass(frozen=True, slots=True)
class Recognition:
    amount: Decimal
    source: Literal["qr", "backend"]


class ReceiptService:
    """Сумма с фото: сначала локальный QR, если не вышло — POST /api/expenses/receipt."""

    def __init__(
        self,
        api: ObshakApiClient,
        auth: AuthService,
        decode_qr: DecodeQr = decode_qr_from_bytes,
    ) -> None:
        self._api = api
        self._auth = auth
        self._decode_qr = decode_qr

    async def recognize(self, actor: TelegramUser, image: bytes) -> Recognition | None:
        payload = self._decode_qr(image)
        if payload:
            amount = parse_fiscal_qr(payload)
            if amount is not None:
                return Recognition(amount, "qr")
            log.info("QR decoded but is not a fiscal receipt: %s", payload[:80])

        try:
            dto = await self._auth.run_authorized(
                actor, lambda token: self._api.upload_receipt(token, image)
            )
        except (ApiError, ApiUnavailable) as exc:
            log.warning("Receipt fallback failed: %s", exc)
            return None
        if dto.amount <= 0:
            return None
        return Recognition(dto.amount, "backend")
