from dataclasses import dataclass
from decimal import Decimal

from obshak_bot.api import DebtDto, ObshakApiClient
from obshak_bot.money import format_amount
from obshak_bot.services.auth import AuthService, TelegramUser
from obshak_bot.services.errors import UserError


@dataclass(frozen=True, slots=True)
class DebtOverview:
    i_owe: list[DebtDto]
    owed_to_me: list[DebtDto]

    @property
    def is_empty(self) -> bool:
        return not self.i_owe and not self.owed_to_me


@dataclass(frozen=True, slots=True)
class Payment:
    debt: DebtDto  # долг до оплаты, с именами сторон
    amount: Decimal
    remaining: Decimal

    @property
    def settled(self) -> bool:
        return self.remaining == 0


class DebtService:
    """Долги в группе: кто кому сколько, и возврат своего долга."""

    def __init__(self, api: ObshakApiClient, auth: AuthService) -> None:
        self._api = api
        self._auth = auth

    async def overview(self, actor: TelegramUser, group_id: str) -> DebtOverview:
        me = (await self._auth.ensure_session(actor)).user_id
        debts = await self._auth.run_authorized(
            actor, lambda token: self._api.group_debts(token, group_id)
        )
        return DebtOverview(
            i_owe=[d for d in debts if d.from_user_id == me],
            owed_to_me=[d for d in debts if d.to_user_id == me],
        )

    async def my_debts(self, actor: TelegramUser) -> DebtOverview:
        """Все непогашенные долги пользователя (по всем группам)."""
        me = (await self._auth.ensure_session(actor)).user_id
        debts = await self._auth.run_authorized(actor, self._api.my_debts)
        return DebtOverview(
            i_owe=[d for d in debts if d.from_user_id == me],
            owed_to_me=[d for d in debts if d.to_user_id == me],
        )

    async def my_debt(self, actor: TelegramUser, group_id: str, debt_id: str) -> DebtDto:
        """Мой непогашенный долг по id. UserError — если его нет или он не мой."""
        overview = await self.overview(actor, group_id)
        debt = next((d for d in overview.i_owe if d.id == debt_id), None)
        if debt is None:
            raise UserError("Этот долг уже погашен или не твой.")
        return debt

    async def pay(
        self, actor: TelegramUser, group_id: str, debt_id: str, amount: Decimal | None
    ) -> Payment:
        """Вернуть долг целиком (amount=None) или частично."""
        debt = await self.my_debt(actor, group_id, debt_id)
        amount = debt.amount if amount is None else amount
        if amount > debt.amount:
            raise UserError(f"Долг всего {format_amount(debt.amount)} — столько вернуть нельзя.")
        await self._auth.run_authorized(
            actor, lambda token: self._api.pay_debt(token, debt.id, float(amount))
        )
        # Остаток считаем сами в Decimal: бэкенд вычитает во float (23.330000000000002).
        return Payment(debt=debt, amount=amount, remaining=debt.amount - amount)
