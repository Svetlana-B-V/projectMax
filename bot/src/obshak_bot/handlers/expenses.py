"""Добавление расхода в личке: сумма → категория → описание → плательщик → участники → доли."""

import secrets
from collections.abc import Awaitable, Callable
from decimal import Decimal
from typing import Any

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from obshak_bot.handlers.achievements import announce_unlocks
from obshak_bot.keyboards import (
    BTN_EXPENSE,
    BTN_RECEIPT,
    ExpenseCb,
    category_picker,
    confirm_expense,
    main_menu,
    participants_picker,
    payer_confirmation,
    payer_picker,
    split_type_picker,
)
from obshak_bot.money import format_amount, parse_amount
from obshak_bot.services import (
    AchievementService,
    AuthService,
    ExpenseDraft,
    ExpenseService,
    GroupService,
    Notifier,
    ReceiptService,
    TelegramUser,
    expense_summary,
    payer_confirmation_request,
    plan_shares,
    remainder_note,
)

router = Router(name="expenses")
router.message.filter(F.chat.type == ChatType.PRIVATE)
router.callback_query.filter(F.message.chat.type == ChatType.PRIVATE)

SKIP = "-"


class ExpenseForm(StatesGroup):
    amount = State()
    photo = State()
    category = State()
    new_category = State()
    description = State()
    payer = State()
    awaiting_payer = State()  # ждём, пока выбранный плательщик подтвердит в личке
    participants = State()
    split_type = State()
    custom_share = State()
    confirm = State()


@router.message(F.text == BTN_EXPENSE)
async def start_expense(
    message: Message, state: FSMContext, auth: AuthService, groups: GroupService
) -> None:
    if not await _begin_expense(message, state, auth, groups):
        return
    data = await state.get_data()
    await state.set_state(ExpenseForm.amount)
    await message.answer(f"Группа «{data['group_name']}». Сколько потратили? (или /cancel)")


@router.message(F.text == BTN_RECEIPT)
async def start_receipt(
    message: Message, state: FSMContext, auth: AuthService, groups: GroupService
) -> None:
    if not await _begin_expense(message, state, auth, groups):
        return
    await state.set_state(ExpenseForm.photo)
    await message.answer("Пришли фото чека с QR (или /cancel).")


@router.message(ExpenseForm.photo, F.photo)
@router.message(ExpenseForm.photo, F.document)
async def got_receipt_photo(
    message: Message,
    state: FSMContext,
    expenses: ExpenseService,
    receipts: ReceiptService,
) -> None:
    if message.from_user is None:
        return
    image = await _download_image(message)
    if image is None:
        await message.answer("Нужно фото чека (не файл другого типа).")
        return
    await message.answer("Смотрю чек…")
    actor = TelegramUser.from_aiogram(message.from_user)
    result = await receipts.recognize(actor, image)
    if result is None:
        await state.set_state(ExpenseForm.amount)
        await message.answer("Не смог прочитать чек. Введи сумму руками.")
        return
    source = "QR" if result.source == "qr" else "сервер (проверь сумму — распознавание примерное)"
    await message.answer(f"Сумма {format_amount(result.amount)} — {source}.")
    await _ask_category(message, state, expenses, actor, result.amount)


@router.message(ExpenseForm.amount, F.text)
async def set_amount(message: Message, state: FSMContext, expenses: ExpenseService) -> None:
    if message.from_user is None or message.text is None:
        return
    amount = parse_amount(message.text)
    if amount is None:
        await message.answer("Не понял сумму. Пример: <code>1250</code> или <code>99,90</code>.")
        return
    await _ask_category(
        message, state, expenses, TelegramUser.from_aiogram(message.from_user), amount
    )


@router.callback_query(ExpenseForm.category, ExpenseCb.filter(F.action == "category"))
async def set_category(
    callback: CallbackQuery, callback_data: ExpenseCb, state: FSMContext
) -> None:
    data = await state.get_data()
    category_id = callback_data.value or None
    await state.update_data(
        category_id=category_id, category_name=data["categories"].get(category_id)
    )
    await callback.answer()
    await _ask_description(callback.message, state)


@router.callback_query(ExpenseForm.category, ExpenseCb.filter(F.action == "new_category"))
async def ask_new_category(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ExpenseForm.new_category)
    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.answer("Название новой категории:")


@router.message(ExpenseForm.new_category, F.text)
async def create_category(message: Message, state: FSMContext, expenses: ExpenseService) -> None:
    if message.from_user is None or message.text is None:
        return
    name = message.text.strip()
    if not name:
        await message.answer("Название не может быть пустым.")
        return
    data = await state.get_data()
    category = await expenses.create_category(
        TelegramUser.from_aiogram(message.from_user), data["group_id"], name
    )
    await state.update_data(category_id=category.id, category_name=category.name)
    await _ask_description(message, state)


@router.message(ExpenseForm.description, F.text)
async def set_description(message: Message, state: FSMContext) -> None:
    if message.text is None:
        return
    description = message.text.strip()
    data = await state.update_data(description=None if description == SKIP else description)
    await state.set_state(ExpenseForm.payer)
    await message.answer("Кто платил?", reply_markup=payer_picker(data["names"], data["me"]))


@router.callback_query(ExpenseForm.payer, ExpenseCb.filter(F.action == "payer"))
async def set_payer(
    callback: CallbackQuery,
    callback_data: ExpenseCb,
    state: FSMContext,
    auth: AuthService,
    notifier: Notifier,
) -> None:
    data = await state.get_data()
    payer_id = callback_data.value
    await state.update_data(payer_id=payer_id)
    await callback.answer()
    if not isinstance(callback.message, Message):
        return

    if payer_id == data["me"]:
        await ask_participants(state, callback.message.edit_text)
        return

    # Платил другой участник — сначала спрашиваем у него самого.
    payer_name = data["names"][payer_id]
    payer_telegram_id = await auth.telegram_id_of(payer_id)
    if payer_telegram_id is None:
        await callback.message.answer(
            f"{payer_name} ещё не открывал бота, поэтому подтвердить оплату не сможет. "
            "Попроси его написать боту /start или выбери другого плательщика."
        )
        return

    actor = TelegramUser.from_aiogram(callback.from_user)
    token = secrets.token_urlsafe(6)
    sent = await notifier.send(
        payer_telegram_id,
        payer_confirmation_request(
            actor.name,
            data["group_name"],
            Decimal(data["amount"]),
            data.get("description"),
            data.get("category_name"),
        ),
        payer_confirmation(initiator=actor.id, token=token),
    )
    if not sent:
        await callback.message.answer(
            f"Не удалось написать {payer_name} — похоже, он заблокировал бота. "
            "Выбери другого плательщика."
        )
        return
    await state.update_data(confirm_token=token)
    await state.set_state(ExpenseForm.awaiting_payer)
    await callback.message.edit_text(
        f"Спросил у {payer_name}, платил ли он. Как ответит — продолжим. Отменить — /cancel."
    )


async def ask_participants(state: FSMContext, reply: Callable[..., Awaitable[Any]]) -> None:
    """Перейти к выбору участников; по умолчанию делим на всех."""
    names: dict[str, str] = (await state.get_data())["names"]
    await state.update_data(participants=list(names))
    await state.set_state(ExpenseForm.participants)
    await reply(
        "На кого делим? Отметь участников:", reply_markup=participants_picker(names, set(names))
    )


@router.callback_query(ExpenseForm.participants, ExpenseCb.filter(F.action.in_({"toggle", "all"})))
async def toggle_participant(
    callback: CallbackQuery, callback_data: ExpenseCb, state: FSMContext
) -> None:
    data = await state.get_data()
    selected = set(data["participants"])
    if callback_data.action == "all":
        selected = set(data["names"])
    elif callback_data.value in selected:
        selected.discard(callback_data.value)
    else:
        selected.add(callback_data.value)
    await state.update_data(participants=sorted(selected))
    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.edit_reply_markup(
            reply_markup=participants_picker(data["names"], selected)
        )


@router.callback_query(ExpenseForm.participants, ExpenseCb.filter(F.action == "done"))
async def participants_done(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    if not data["participants"]:
        await callback.answer("Выбери хотя бы одного участника", show_alert=True)
        return
    await callback.answer()
    if len(data["participants"]) == 1:
        await state.update_data(custom=None)
        await _show_confirmation(callback.message, state)
        return
    await state.set_state(ExpenseForm.split_type)
    await _edit(callback, "Как делим?", split_type_picker())


@router.callback_query(ExpenseForm.split_type, ExpenseCb.filter(F.action == "split"))
async def set_split_type(
    callback: CallbackQuery, callback_data: ExpenseCb, state: FSMContext
) -> None:
    await callback.answer()
    if callback_data.value == "equal":
        await state.update_data(custom=None)
        await _show_confirmation(callback.message, state)
        return
    participants = (await state.get_data())["participants"]
    data = await state.update_data(custom={}, pending=list(participants))
    await state.set_state(ExpenseForm.custom_share)
    await _ask_next_share(callback.message, data)


@router.message(ExpenseForm.custom_share, F.text)
async def set_custom_share(message: Message, state: FSMContext) -> None:
    if message.text is None:
        return
    data = await state.get_data()
    remaining = _remaining(data)
    share = parse_amount(message.text)
    if share is None or share > remaining:
        await message.answer(
            f"Нужна сумма от 0,01 до {format_amount(remaining)}. Попробуй ещё раз."
        )
        return
    pending: list[str] = data["pending"]
    custom: dict[str, str] = data["custom"]
    custom[pending.pop(0)] = str(share)
    data = await state.update_data(custom=custom, pending=pending)
    if len(pending) == 1:  # последнему — всё, что осталось, чтобы сумма сошлась
        custom[pending.pop(0)] = str(_remaining(data))
        await state.update_data(custom=custom, pending=pending)
    if not pending:
        await _show_confirmation(message, state)
        return
    await _ask_next_share(message, data)


@router.callback_query(ExpenseForm.confirm, ExpenseCb.filter(F.action == "cancel"))
async def cancel_expense(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer()
    if isinstance(callback.message, Message):
        await callback.message.edit_text("Расход не сохранён.")


@router.callback_query(ExpenseForm.confirm, ExpenseCb.filter(F.action == "save"))
async def save_expense(
    callback: CallbackQuery,
    state: FSMContext,
    expenses: ExpenseService,
    notifier: Notifier,
    achievements: AchievementService,
) -> None:
    data = await state.get_data()
    await state.clear()
    actor = TelegramUser.from_aiogram(callback.from_user)
    draft = _draft(data)
    result = await expenses.create(actor, draft)
    await callback.answer("Сохранено")

    text = expense_summary(draft, result.plan, data["names"], data.get("category_name"))
    note = remainder_note(result, data["names"].get(draft.payer_id, "?"))
    if note:
        text += f"\n\n{note}"
    if isinstance(callback.message, Message):
        await callback.message.edit_text(f"Расход сохранён.\n\n{text}")
        await callback.message.answer("Что дальше?", reply_markup=main_menu())

    await notifier.expense_created(
        actor, draft.group_id, data["group_name"], text, list(draft.participant_ids)
    )
    if isinstance(callback.message, Message):
        await announce_unlocks(callback.message, actor, achievements)


# --- helpers ---


async def _begin_expense(
    message: Message, state: FSMContext, auth: AuthService, groups: GroupService
) -> bool:
    """Подготовить FSM расхода. False — нет текущей группы."""
    if message.from_user is None:
        return False
    actor = TelegramUser.from_aiogram(message.from_user)
    group = await groups.current(actor)
    if group is None:
        await message.answer("Сначала выбери группу в «👥 Группы».")
        return False
    session = await auth.ensure_session(actor)
    members = await groups.members(actor, group.id)
    await state.set_data(
        {
            "group_id": group.id,
            "group_name": group.name,
            "me": session.user_id,
            "names": {m.user_id: m.user.name for m in members},
        }
    )
    return True


async def _ask_category(
    message: Message,
    state: FSMContext,
    expenses: ExpenseService,
    actor: TelegramUser,
    amount: Decimal,
) -> None:
    data = await state.get_data()
    categories = await expenses.categories(actor, data["group_id"])
    await state.update_data(amount=str(amount), categories={c.id: c.name for c in categories})
    await state.set_state(ExpenseForm.category)
    await message.answer("Категория:", reply_markup=category_picker(categories))


async def _download_image(message: Message) -> bytes | None:
    if message.photo:
        buffer = await message.bot.download(message.photo[-1])
        return buffer.read() if buffer else None
    doc = message.document
    if doc is not None and (doc.mime_type or "").startswith("image/"):
        buffer = await message.bot.download(doc)
        return buffer.read() if buffer else None
    return None


def _remaining(data: dict[str, Any]) -> Decimal:
    spent = sum((Decimal(v) for v in data["custom"].values()), Decimal(0))
    return Decimal(data["amount"]) - spent


def _draft(data: dict[str, Any]) -> ExpenseDraft:
    custom = data.get("custom")
    return ExpenseDraft(
        group_id=data["group_id"],
        payer_id=data["payer_id"],
        amount=Decimal(data["amount"]),
        participant_ids=tuple(data["participants"]),
        category_id=data.get("category_id"),
        description=data.get("description"),
        custom_shares={uid: Decimal(v) for uid, v in custom.items()} if custom else None,
    )


async def _ask_description(message: Message | Any, state: FSMContext) -> None:
    await state.set_state(ExpenseForm.description)
    if isinstance(message, Message):
        await message.answer(f"На что потратили? Одной строкой, или «{SKIP}», чтобы пропустить.")


async def _ask_next_share(message: Message | Any, data: dict[str, Any]) -> None:
    if not isinstance(message, Message):
        return
    next_id = data["pending"][0]
    await message.answer(
        f"Сколько должен {data['names'][next_id]}? Осталось распределить "
        f"{format_amount(_remaining(data))}."
    )


async def _show_confirmation(message: Message | Any, state: FSMContext) -> None:
    data = await state.get_data()
    draft = _draft(data)
    plan = plan_shares(draft)
    text = expense_summary(draft, plan, data["names"], data.get("category_name"))
    if plan.remainder > 0:
        text += (
            f"\n\nОстаток {format_amount(plan.remainder)} уйдёт в копилку группы "
            "(если её нет — останется у плательщика)."
        )
    await state.set_state(ExpenseForm.confirm)
    if isinstance(message, Message):
        await message.answer(text, reply_markup=confirm_expense())


async def _edit(callback: CallbackQuery, text: str, markup: InlineKeyboardMarkup) -> None:
    if isinstance(callback.message, Message):
        await callback.message.edit_text(text, reply_markup=markup)
