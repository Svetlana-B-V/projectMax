"""Долги текущей группы: кто кому сколько, возврат своего долга целиком или частично."""

from decimal import Decimal

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, User

from obshak_bot.handlers.achievements import announce_unlocks
from obshak_bot.keyboards import BTN_DEBTS, DebtCb, debts_menu, main_menu, pay_all_button
from obshak_bot.money import format_amount, parse_amount
from obshak_bot.services import (
    AchievementService,
    DebtOverview,
    DebtService,
    GroupService,
    Notifier,
    TelegramUser,
    payment_summary,
)

router = Router(name="debts")
router.message.filter(F.chat.type == ChatType.PRIVATE)
router.callback_query.filter(F.message.chat.type == ChatType.PRIVATE)


class PayForm(StatesGroup):
    amount = State()


@router.message(F.text == BTN_DEBTS)
async def show_debts(
    message: Message, state: FSMContext, groups: GroupService, debts: DebtService
) -> None:
    if message.from_user is None:
        return
    actor = TelegramUser.from_aiogram(message.from_user)
    group = await groups.current(actor)
    if group is None:
        await message.answer("Сначала выбери группу в «👥 Группы».")
        return
    await state.update_data(group_id=group.id, group_name=group.name)
    overview = await debts.overview(actor, group.id)
    await message.answer(
        _overview_text(group.name, overview), reply_markup=debts_menu(overview.i_owe)
    )


@router.callback_query(DebtCb.filter(F.action == "refresh"))
async def refresh_debts(callback: CallbackQuery, state: FSMContext, debts: DebtService) -> None:
    data = await state.get_data()
    actor = TelegramUser.from_aiogram(callback.from_user)
    overview = await debts.overview(actor, data["group_id"])
    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            _overview_text(data["group_name"], overview), reply_markup=debts_menu(overview.i_owe)
        )


@router.callback_query(DebtCb.filter(F.action == "pay"))
async def ask_pay_amount(
    callback: CallbackQuery, callback_data: DebtCb, state: FSMContext, debts: DebtService
) -> None:
    data = await state.get_data()
    actor = TelegramUser.from_aiogram(callback.from_user)
    debt = await debts.my_debt(actor, data["group_id"], callback_data.value)
    await state.update_data(debt_id=debt.id)
    await state.set_state(PayForm.amount)
    await callback.answer()
    creditor = debt.to_user.name if debt.to_user else "?"
    if isinstance(callback.message, Message):
        await callback.message.answer(
            f"Сколько вернул {creditor}? Долг — {format_amount(debt.amount)}. "
            "Введи сумму или нажми кнопку (или /cancel).",
            reply_markup=pay_all_button(),
        )


@router.callback_query(PayForm.amount, DebtCb.filter(F.action == "pay_all"))
async def pay_all(
    callback: CallbackQuery,
    state: FSMContext,
    debts: DebtService,
    notifier: Notifier,
    achievements: AchievementService,
) -> None:
    await callback.answer()
    if isinstance(callback.message, Message):
        await _pay(
            callback.message, callback.from_user, state, debts, notifier, achievements, None
        )


@router.message(PayForm.amount, F.text)
async def pay_partially(
    message: Message,
    state: FSMContext,
    debts: DebtService,
    notifier: Notifier,
    achievements: AchievementService,
) -> None:
    if message.from_user is None or message.text is None:
        return
    amount = parse_amount(message.text)
    if amount is None:
        await message.answer("Не понял сумму. Пример: <code>500</code> или <code>250,50</code>.")
        return
    await _pay(message, message.from_user, state, debts, notifier, achievements, amount)


async def _pay(
    message: Message,
    from_user: User,
    state: FSMContext,
    debts: DebtService,
    notifier: Notifier,
    achievements: AchievementService,
    amount: Decimal | None,
) -> None:
    data = await state.get_data()
    await state.set_state(None)
    actor = TelegramUser.from_aiogram(from_user)
    payment = await debts.pay(actor, data["group_id"], data["debt_id"], amount)
    await message.answer(payment_summary(payment), reply_markup=main_menu())
    await notifier.debt_paid(actor, data["group_name"], payment)
    await announce_unlocks(message, actor, achievements)

    overview = await debts.overview(actor, data["group_id"])
    await message.answer(
        _overview_text(data["group_name"], overview), reply_markup=debts_menu(overview.i_owe)
    )


def _overview_text(group_name: str, overview: DebtOverview) -> str:
    if overview.is_empty:
        return f"Группа «{group_name}»: долгов нет 🎉"
    lines = [f"Долги в группе «{group_name}»"]
    if overview.i_owe:
        lines.append("\n<b>Я должен:</b>")
        lines.extend(
            f"  • {d.to_user.name if d.to_user else '?'} — {format_amount(d.amount)}"
            for d in overview.i_owe
        )
    if overview.owed_to_me:
        lines.append("\n<b>Мне должны:</b>")
        lines.extend(
            f"  • {d.from_user.name if d.from_user else '?'} — {format_amount(d.amount)}"
            for d in overview.owed_to_me
        )
    return "\n".join(lines)
