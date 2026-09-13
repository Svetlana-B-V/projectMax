import logging
from collections.abc import Mapping
from decimal import Decimal

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import InlineKeyboardMarkup

from obshak_bot.money import format_amount
from obshak_bot.services.auth import TelegramUser
from obshak_bot.services.debts import Payment
from obshak_bot.services.expenses import ExpenseDraft, ExpensePlan, ExpenseResult
from obshak_bot.storage import ChatGroupRepository, UserSessionRepository

log = logging.getLogger(__name__)


def expense_summary(
    draft: ExpenseDraft,
    plan: ExpensePlan,
    names: Mapping[str, str],
    category_name: str | None,
) -> str:
    """Текст карточки расхода — для подтверждения и для уведомлений."""
    lines = [f"💸 <b>{format_amount(draft.amount)}</b>"]
    if draft.description:
        lines.append(f"На что: {draft.description}")
    lines.append(f"Категория: {category_name or 'без категории'}")
    lines.append(f"Платил: {names.get(draft.payer_id, '?')}")
    lines.append("Делим:")
    lines.extend(
        f"  • {names.get(uid, '?')} — {format_amount(share)}" for uid, share in plan.shares.items()
    )
    return "\n".join(lines)


def remainder_note(result: ExpenseResult, payer_name: str) -> str | None:
    remainder = result.plan.remainder
    if remainder <= 0:
        return None
    if result.piggy_bank is not None:
        return f"Остаток {format_amount(remainder)} отправлен в копилку «{result.piggy_bank.name}»."
    return f"Остаток {format_amount(remainder)} остался у плательщика ({payer_name})."


def payer_confirmation_request(
    initiator_name: str,
    group_name: str,
    amount: Decimal,
    description: str | None,
    category_name: str | None,
) -> str:
    """Вопрос предполагаемому плательщику: действительно ли он платил."""
    what = f" на «{description}»" if description else ""
    return (
        f"{initiator_name} добавляет расход в группе «{group_name}»: "
        f"<b>{format_amount(amount)}</b>{what}, категория — {category_name or 'без категории'}.\n"
        f"Указано, что платил ты. Подтверждаешь?"
    )


def payment_summary(payment: Payment) -> str:
    """«Вернул 500 ₽. Остаток 200 ₽» / «Долг закрыт»."""
    tail = (
        "Долг закрыт ✅"
        if payment.settled
        else f"Осталось вернуть {format_amount(payment.remaining)}."
    )
    return f"Возврат {format_amount(payment.amount)}. {tail}"


class Notifier:
    """Уведомления участникам: в привязанный чат группы либо в личку."""

    def __init__(
        self, bot: Bot, sessions: UserSessionRepository, chats: ChatGroupRepository
    ) -> None:
        self._bot = bot
        self._sessions = sessions
        self._chats = chats

    async def expense_created(
        self,
        actor: TelegramUser,
        group_id: str,
        group_name: str,
        text: str,
        participant_ids: list[str],
    ) -> None:
        header = f"{actor.name} добавил расход в группе «{group_name}»:\n\n"
        binding = await self._chats.find_by_group(group_id)
        if binding is not None:
            await self.send(binding.chat_id, header + text)
            return
        telegram_ids = await self._sessions.telegram_ids(participant_ids)
        for telegram_id in telegram_ids.values():
            if telegram_id != actor.id:
                await self.send(telegram_id, header + text)

    async def debt_paid(self, actor: TelegramUser, group_name: str, payment: Payment) -> None:
        """Кредитору в личку: кто, сколько и что осталось."""
        creditor = payment.debt.to_user
        if creditor is None or creditor.telegram_id is None:
            return
        await self.send(
            creditor.telegram_id,
            f"{actor.name} вернул тебе долг в группе «{group_name}».\n{payment_summary(payment)}",
        )

    async def send(
        self, chat_id: int, text: str, reply_markup: InlineKeyboardMarkup | None = None
    ) -> bool:
        """Отправить сообщение; False — если Telegram не дал (не открывал бота, заблокировал…)."""
        try:
            await self._bot.send_message(chat_id, text, reply_markup=reply_markup)
        except TelegramAPIError as exc:
            log.info("Notification to %s skipped: %s", chat_id, exc)
            return False
        return True
