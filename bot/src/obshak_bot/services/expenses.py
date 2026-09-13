import logging
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal

from obshak_bot.api import (
    ApiError,
    ApiUnavailable,
    CategoryDto,
    ExpenseCreate,
    ExpenseDto,
    ObshakApiClient,
    SavingsGoalDto,
    SplitInput,
)
from obshak_bot.money import split_equally
from obshak_bot.services.auth import AuthService, TelegramUser

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ExpenseDraft:
    """Расход, собранный в диалоге с пользователем, но ещё не отправленный в бэкенд."""

    group_id: str
    payer_id: str
    amount: Decimal
    participant_ids: tuple[str, ...]
    category_id: str | None = None
    description: str | None = None
    custom_shares: Mapping[str, Decimal] | None = None  # None — делим поровну


@dataclass(frozen=True, slots=True)
class ExpensePlan:
    """Кто сколько должен и что осталось нераспределённым после деления поровну."""

    shares: dict[str, Decimal]
    remainder: Decimal


@dataclass(frozen=True, slots=True)
class ExpenseResult:
    expense: ExpenseDto
    plan: ExpensePlan
    piggy_bank: SavingsGoalDto | None  # копилка, куда ушёл остаток; None — остаток у плательщика


def plan_shares(draft: ExpenseDraft) -> ExpensePlan:
    """Чистый расчёт долей: поровну (остаток — отдельно) или по введённым суммам."""
    if not draft.participant_ids:
        raise ValueError("Нужен хотя бы один участник")
    if draft.custom_shares is None:
        share, remainder = split_equally(draft.amount, len(draft.participant_ids))
        return ExpensePlan({uid: share for uid in draft.participant_ids}, remainder)

    shares = {uid: draft.custom_shares[uid] for uid in draft.participant_ids}
    if sum(shares.values(), Decimal(0)) != draft.amount:
        raise ValueError("Сумма долей не совпадает с суммой расхода")
    return ExpensePlan(shares, Decimal(0))


class ExpenseService:
    """Добавление расходов: категории, доли, отправка в бэкенд, остаток — в копилку группы."""

    def __init__(self, api: ObshakApiClient, auth: AuthService) -> None:
        self._api = api
        self._auth = auth

    async def categories(self, actor: TelegramUser, group_id: str) -> list[CategoryDto]:
        return await self._auth.run_authorized(
            actor, lambda token: self._api.categories(token, group_id)
        )

    async def create_category(self, actor: TelegramUser, group_id: str, name: str) -> CategoryDto:
        return await self._auth.run_authorized(
            actor, lambda token: self._api.create_category(token, group_id, name)
        )

    async def create(self, actor: TelegramUser, draft: ExpenseDraft) -> ExpenseResult:
        plan = plan_shares(draft)
        payload = ExpenseCreate(
            group_id=draft.group_id,
            payer_id=draft.payer_id,
            amount=float(draft.amount),
            category_id=draft.category_id,
            description=draft.description,
            splits=[
                SplitInput(user_id=uid, amount_owed=float(s)) for uid, s in plan.shares.items()
            ],
        )
        expense = await self._auth.run_authorized(
            actor, lambda token: self._api.create_expense(token, payload)
        )
        piggy_bank = None
        if plan.remainder > 0:
            piggy_bank = await self._put_remainder_to_piggy_bank(actor, draft, plan.remainder)
        return ExpenseResult(expense, plan, piggy_bank)

    async def _put_remainder_to_piggy_bank(
        self, actor: TelegramUser, draft: ExpenseDraft, remainder: Decimal
    ) -> SavingsGoalDto | None:
        """Остаток — в активную общую копилку группы. Нет копилки — остаётся у плательщика."""
        try:
            goals = await self._auth.run_authorized(
                actor, lambda token: self._api.savings_goals(token, draft.group_id)
            )
            goal = next((g for g in goals if g.type == "group" and g.status == "active"), None)
            if goal is None:
                return None
            note = f"Остаток от расхода «{draft.description}»" if draft.description else None
            return await self._auth.run_authorized(
                actor, lambda token: self._api.contribute(token, goal.id, float(remainder), note)
            )
        except (ApiError, ApiUnavailable) as exc:
            # Расход уже сохранён; копилка — приятное дополнение, не ломаем из-за неё сценарий.
            log.warning("Remainder %s not moved to piggy bank: %s", remainder, exc)
            return None
