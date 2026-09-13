import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from obshak_bot.api import DebtDto, ObshakApiClient, ReminderSettingsDto
from obshak_bot.money import format_amount
from obshak_bot.services.auth import AuthService, TelegramUser
from obshak_bot.services.debts import DebtService
from obshak_bot.services.errors import UserError

log = logging.getLogger(__name__)

STYLES = ("soft", "neutral", "playful")
STYLE_LABELS = {"soft": "мягкий", "neutral": "нейтральный", "playful": "шутливый"}


class ReminderService:
    """Настройки напоминаний о долгах и текст очередного напоминания."""

    def __init__(
        self,
        api: ObshakApiClient,
        auth: AuthService,
        debts: DebtService,
        interval_hours: float,
    ) -> None:
        self._api = api
        self._auth = auth
        self._debts = debts
        self._interval = timedelta(hours=interval_hours)

    async def settings(self, actor: TelegramUser) -> ReminderSettingsDto:
        return await self._auth.run_authorized(actor, self._api.reminder_settings)

    async def set_style(self, actor: TelegramUser, style: str) -> ReminderSettingsDto:
        if style not in STYLES:
            raise UserError("Неизвестный стиль напоминаний.")
        return await self._auth.run_authorized(
            actor, lambda token: self._api.update_reminder_settings(token, style=style)
        )

    async def set_enabled(self, actor: TelegramUser, enabled: bool) -> ReminderSettingsDto:
        return await self._auth.run_authorized(
            actor, lambda token: self._api.update_reminder_settings(token, enabled=enabled)
        )

    async def ack(self, actor: TelegramUser) -> None:
        await self._auth.run_authorized(actor, self._api.ack_reminder)

    async def due_text(self, actor: TelegramUser, *, force: bool = False) -> str | None:
        """Текст напоминания или None, если напоминать не о чем / ещё рано."""
        settings = await self.settings(actor)
        if not settings.enabled:
            return None
        if not force and not _is_due(settings.last_reminded_at, self._interval):
            return None
        overview = await self._debts.my_debts(actor)
        if not overview.i_owe:
            return None
        return render_debt_reminder(settings.style, overview.i_owe)


def render_debt_reminder(style: str, i_owe: list[DebtDto]) -> str:
    total = sum((d.amount for d in i_owe), Decimal(0))
    lines = "\n".join(f"  • {_creditor(d)} — {format_amount(d.amount)}" for d in i_owe)
    if style == "soft":
        return f"Привет! Небольшое напоминание: за тобой ещё {format_amount(total)}.\n{lines}"
    if style == "playful":
        return f"Кошелёк шепчет: за тобой {format_amount(total)}. Самое время вернуть 🦸\n{lines}"
    return f"Напоминание о долгах: {format_amount(total)}.\n{lines}"


def _creditor(debt: DebtDto) -> str:
    return debt.to_user.name if debt.to_user else "?"


def _is_due(last_reminded_at: str | None, interval: timedelta) -> bool:
    if not last_reminded_at:
        return True
    try:
        last = datetime.fromisoformat(last_reminded_at.replace("Z", "+00:00"))
    except ValueError:
        return True
    if last.tzinfo is None:
        last = last.replace(tzinfo=UTC)
    return datetime.now(UTC) - last >= interval
