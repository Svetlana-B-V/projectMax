"""Копилки текущей группы: список с прогрессом, создание, взнос."""

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from obshak_bot.api import SavingsGoalDto
from obshak_bot.handlers.achievements import announce_unlocks
from obshak_bot.keyboards import BTN_PIGGY, PiggyCb, main_menu, piggy_menu
from obshak_bot.money import format_amount, parse_amount
from obshak_bot.services import (
    AchievementService,
    GroupService,
    PiggyBankService,
    TelegramUser,
    progress_line,
)

router = Router(name="piggy")
router.message.filter(F.chat.type == ChatType.PRIVATE)
router.callback_query.filter(F.message.chat.type == ChatType.PRIVATE)


class PiggyForm(StatesGroup):
    name = State()
    target = State()
    contribute_amount = State()


@router.message(F.text == BTN_PIGGY)
async def show_piggy(
    message: Message, state: FSMContext, groups: GroupService, piggy: PiggyBankService
) -> None:
    if message.from_user is None:
        return
    actor = TelegramUser.from_aiogram(message.from_user)
    group = await groups.current(actor)
    if group is None:
        await message.answer("Сначала выбери группу в «👥 Группы».")
        return
    await state.update_data(group_id=group.id, group_name=group.name)
    goals = await piggy.list(actor, group.id)
    await message.answer(_list_text(group.name, goals), reply_markup=piggy_menu(goals))


@router.callback_query(PiggyCb.filter(F.action == "refresh"))
async def refresh_piggy(
    callback: CallbackQuery, state: FSMContext, piggy: PiggyBankService
) -> None:
    data = await state.get_data()
    actor = TelegramUser.from_aiogram(callback.from_user)
    goals = await piggy.list(actor, data["group_id"])
    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            _list_text(data["group_name"], goals), reply_markup=piggy_menu(goals)
        )


@router.callback_query(PiggyCb.filter(F.action == "create"))
async def ask_piggy_name(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(PiggyForm.name)
    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.answer("Как назовём копилку? (или /cancel)")


@router.message(PiggyForm.name, F.text)
async def set_piggy_name(message: Message, state: FSMContext) -> None:
    if message.text is None:
        return
    name = message.text.strip()
    if not name:
        await message.answer("Название не может быть пустым.")
        return
    await state.update_data(piggy_name=name)
    await state.set_state(PiggyForm.target)
    await message.answer("Какая цель в рублях?")


@router.message(PiggyForm.target, F.text)
async def create_piggy(
    message: Message, state: FSMContext, piggy: PiggyBankService, achievements: AchievementService
) -> None:
    if message.from_user is None or message.text is None:
        return
    target = parse_amount(message.text)
    if target is None:
        await message.answer("Не понял сумму. Пример: <code>10000</code>.")
        return
    data = await state.get_data()
    await state.set_state(None)
    actor = TelegramUser.from_aiogram(message.from_user)
    goal = await piggy.create(actor, data["group_id"], data["piggy_name"], target)
    await message.answer(f"Копилка создана.\n{progress_line(goal)}", reply_markup=main_menu())
    await announce_unlocks(message, actor, achievements)
    goals = await piggy.list(actor, data["group_id"])
    await message.answer(_list_text(data["group_name"], goals), reply_markup=piggy_menu(goals))


@router.callback_query(PiggyCb.filter(F.action == "contrib"))
async def ask_contribution(
    callback: CallbackQuery, callback_data: PiggyCb, state: FSMContext, piggy: PiggyBankService
) -> None:
    data = await state.get_data()
    actor = TelegramUser.from_aiogram(callback.from_user)
    goal = await piggy.active_goal(actor, data["group_id"], callback_data.value)
    await state.update_data(goal_id=goal.id, goal_name=goal.name)
    await state.set_state(PiggyForm.contribute_amount)
    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.answer(
            f"Сколько кладём в «{goal.name}»? Сейчас {format_amount(goal.current_amount)} "
            f"из {format_amount(goal.target_amount)}."
        )


@router.message(PiggyForm.contribute_amount, F.text)
async def contribute(
    message: Message, state: FSMContext, piggy: PiggyBankService, achievements: AchievementService
) -> None:
    if message.from_user is None or message.text is None:
        return
    amount = parse_amount(message.text)
    if amount is None:
        await message.answer("Не понял сумму. Пример: <code>500</code>.")
        return
    data = await state.get_data()
    await state.set_state(None)
    actor = TelegramUser.from_aiogram(message.from_user)
    goal = await piggy.contribute(actor, data["goal_id"], amount)
    note = (
        f"Цель «{goal.name}» достигнута 🎉"
        if goal.status == "completed" or goal.current_amount >= goal.target_amount
        else progress_line(goal)
    )
    await message.answer(f"Взнос {format_amount(amount)} принят.\n{note}", reply_markup=main_menu())
    await announce_unlocks(message, actor, achievements)
    goals = await piggy.list(actor, data["group_id"])
    await message.answer(_list_text(data["group_name"], goals), reply_markup=piggy_menu(goals))


def _list_text(group_name: str, goals: list[SavingsGoalDto]) -> str:
    if not goals:
        return (
            f"В группе «{group_name}» копилок нет. "
            "Создай первую — туда же уйдёт остаток от деления расходов."
        )
    lines = [f"Копилки группы «{group_name}»", ""]
    lines.extend(progress_line(g) for g in goals)
    return "\n".join(lines)
