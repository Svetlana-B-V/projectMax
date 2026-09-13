from decimal import Decimal

from obshak_bot.api import ObshakApiClient, SavingsGoalDto
from obshak_bot.money import format_amount
from obshak_bot.services.auth import AuthService, TelegramUser
from obshak_bot.services.errors import UserError

BAR_WIDTH = 10


class PiggyBankService:
    """Копилки группы: список, создание общей копилки, взнос."""

    def __init__(self, api: ObshakApiClient, auth: AuthService) -> None:
        self._api = api
        self._auth = auth

    async def list(self, actor: TelegramUser, group_id: str) -> list[SavingsGoalDto]:
        return await self._auth.run_authorized(
            actor, lambda token: self._api.savings_goals(token, group_id)
        )

    async def create(
        self, actor: TelegramUser, group_id: str, name: str, target: Decimal
    ) -> SavingsGoalDto:
        return await self._auth.run_authorized(
            actor, lambda token: self._api.create_savings_goal(token, group_id, name, float(target))
        )

    async def contribute(
        self, actor: TelegramUser, goal_id: str, amount: Decimal, note: str | None = None
    ) -> SavingsGoalDto:
        return await self._auth.run_authorized(
            actor, lambda token: self._api.contribute(token, goal_id, float(amount), note)
        )

    async def active_goal(self, actor: TelegramUser, group_id: str, goal_id: str) -> SavingsGoalDto:
        goal = next((g for g in await self.list(actor, group_id) if g.id == goal_id), None)
        if goal is None:
            raise UserError("Такой копилки нет в этой группе.")
        if goal.status != "active":
            raise UserError(f"Копилка «{goal.name}» уже закрыта.")
        return goal


def progress_line(goal: SavingsGoalDto) -> str:
    """«На отпуск — 250,00 ₽ / 10 000,00 ₽ (2%)  ██░░░░░░░░»."""
    pct = 0 if goal.target_amount <= 0 else int(goal.current_amount / goal.target_amount * 100)
    filled = min(BAR_WIDTH, max(0, pct * BAR_WIDTH // 100))
    bar = "█" * filled + "░" * (BAR_WIDTH - filled)
    mark = " ✅" if goal.status == "completed" or goal.current_amount >= goal.target_amount else ""
    return (
        f"🐷 <b>{goal.name}</b>{mark}\n"
        f"   {format_amount(goal.current_amount)} / {format_amount(goal.target_amount)} "
        f"({min(pct, 100)}%)  {bar}"
    )
