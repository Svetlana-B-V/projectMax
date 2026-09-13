from aiogram import Bot, F, Router
from aiogram.enums import ChatType
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from obshak_bot.api import GroupDto
from obshak_bot.handlers.achievements import announce_unlocks
from obshak_bot.handlers.start import INVITE_PREFIX
from obshak_bot.keyboards import BTN_GROUPS, GroupCb, group_card, groups_menu
from obshak_bot.services import AchievementService, AuthService, GroupService, TelegramUser

router = Router(name="groups_private")
router.message.filter(F.chat.type == ChatType.PRIVATE)
router.callback_query.filter(F.message.chat.type == ChatType.PRIVATE)


class GroupForm(StatesGroup):
    name = State()
    invite_code = State()


@router.message(F.text == BTN_GROUPS)
async def show_groups(message: Message, auth: AuthService, groups: GroupService) -> None:
    if message.from_user is None:
        return
    actor = TelegramUser.from_aiogram(message.from_user)
    session = await auth.ensure_session(actor)
    my_groups = await groups.list_my(actor)
    await message.answer(
        _groups_text(my_groups), reply_markup=groups_menu(my_groups, session.current_group_id)
    )


@router.callback_query(GroupCb.filter(F.action == "back"))
async def back_to_groups(callback: CallbackQuery, auth: AuthService, groups: GroupService) -> None:
    actor = TelegramUser.from_aiogram(callback.from_user)
    session = await auth.ensure_session(actor)
    my_groups = await groups.list_my(actor)
    await _edit(callback, _groups_text(my_groups), groups_menu(my_groups, session.current_group_id))


@router.callback_query(GroupCb.filter(F.action == "select"))
async def select_group(
    callback: CallbackQuery, callback_data: GroupCb, groups: GroupService
) -> None:
    actor = TelegramUser.from_aiogram(callback.from_user)
    group = await groups.select_current(actor, callback_data.group_id)
    await _edit(callback, _group_text(group), group_card(group))


@router.callback_query(GroupCb.filter(F.action == "members"))
async def show_members(
    callback: CallbackQuery, callback_data: GroupCb, groups: GroupService
) -> None:
    actor = TelegramUser.from_aiogram(callback.from_user)
    members = await groups.members(actor, callback_data.group_id)
    group = await groups.select_current(actor, callback_data.group_id)
    lines = [f"• {m.user.name}" + (" — владелец" if m.role == "owner" else "") for m in members]
    await _edit(
        callback, f"{_group_text(group)}\n\nУчастники:\n" + "\n".join(lines), group_card(group)
    )


@router.callback_query(GroupCb.filter(F.action == "invite"))
async def show_invite(
    callback: CallbackQuery, callback_data: GroupCb, groups: GroupService, bot: Bot
) -> None:
    actor = TelegramUser.from_aiogram(callback.from_user)
    group = await groups.select_current(actor, callback_data.group_id)
    me = await bot.me()
    link = f"https://t.me/{me.username}?start={INVITE_PREFIX}{group.invite_code}"
    await _edit(
        callback,
        f"{_group_text(group)}\n\nКод приглашения: <code>{group.invite_code}</code>\n"
        f"Ссылка: {link}",
        group_card(group),
    )


@router.callback_query(GroupCb.filter(F.action == "create"))
async def ask_group_name(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(GroupForm.name)
    await callback.answer()
    if callback.message is not None:
        await callback.message.answer("Как назовём группу? (или /cancel)")


@router.message(GroupForm.name, F.text)
async def create_group(
    message: Message, state: FSMContext, groups: GroupService, achievements: AchievementService
) -> None:
    if message.from_user is None or message.text is None:
        return
    name = message.text.strip()
    if not name:
        await message.answer("Название не может быть пустым. Попробуй ещё раз.")
        return
    actor = TelegramUser.from_aiogram(message.from_user)
    group = await groups.create(actor, name)
    await state.clear()
    await message.answer(
        f"Группа «{group.name}» создана.\n{_group_text(group)}", reply_markup=group_card(group)
    )
    await announce_unlocks(message, actor, achievements)


@router.callback_query(GroupCb.filter(F.action == "join"))
async def ask_invite_code(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(GroupForm.invite_code)
    await callback.answer()
    if callback.message is not None:
        await callback.message.answer("Введи код приглашения (или /cancel):")


@router.message(GroupForm.invite_code, F.text)
async def join_group(message: Message, state: FSMContext, groups: GroupService) -> None:
    if message.from_user is None or message.text is None:
        return
    group = await groups.join_by_code(
        TelegramUser.from_aiogram(message.from_user), message.text.strip().upper()
    )
    await state.clear()
    await message.answer(f"Ты вступил в группу «{group.name}».", reply_markup=group_card(group))


def _groups_text(groups: list[GroupDto]) -> str:
    if not groups:
        return "У тебя пока нет групп. Создай новую или вступи по коду."
    return "Твои группы (✅ — текущая). Нажми на группу, чтобы выбрать её:"


def _group_text(group: GroupDto) -> str:
    return f"Группа <b>{group.name}</b> выбрана как текущая."


async def _edit(callback: CallbackQuery, text: str, markup: InlineKeyboardMarkup) -> None:
    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.edit_text(text, reply_markup=markup)
