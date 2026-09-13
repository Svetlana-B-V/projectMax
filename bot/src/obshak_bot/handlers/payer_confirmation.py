"""Ответ плательщика «да/нет» — продолжает или обрывает диалог того, кто добавляет расход."""

from aiogram import Bot, F, Router
from aiogram.enums import ChatType
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import CallbackQuery, Message

from obshak_bot.handlers.expenses import ExpenseForm, ask_participants
from obshak_bot.keyboards import PayerConfirmCb, main_menu

router = Router(name="payer_confirmation")
router.callback_query.filter(F.message.chat.type == ChatType.PRIVATE)


@router.callback_query(PayerConfirmCb.filter())
async def payer_decision(
    callback: CallbackQuery, callback_data: PayerConfirmCb, bot: Bot, state: FSMContext
) -> None:
    initiator = FSMContext(
        storage=state.storage,
        key=StorageKey(
            bot_id=bot.id, chat_id=callback_data.initiator, user_id=callback_data.initiator
        ),
    )
    if not await is_pending_confirmation(initiator, callback_data.token):
        await callback.answer("Этот запрос уже не актуален.", show_alert=True)
        await _finish(callback, "Запрос устарел.")
        return

    payer_name = callback.from_user.full_name
    if callback_data.decision == "yes":
        await callback.answer("Спасибо!")
        await _finish(callback, "Оплата подтверждена ✅")
        await bot.send_message(callback_data.initiator, f"{payer_name} подтвердил оплату.")
        await ask_participants(
            initiator, lambda text, **kw: bot.send_message(callback_data.initiator, text, **kw)
        )
        return

    await callback.answer()
    await _finish(callback, "Ты ответил, что не платил ❌")
    await initiator.clear()
    await bot.send_message(
        callback_data.initiator,
        f"{payer_name} не подтвердил оплату. Расход отменён.",
        reply_markup=main_menu(),
    )


async def is_pending_confirmation(initiator: FSMContext, token: str) -> bool:
    """True, если инициатор всё ещё ждёт ответ на этот конкретный запрос."""
    data = await initiator.get_data()
    return (
        await initiator.get_state() == ExpenseForm.awaiting_payer.state
        and data.get("confirm_token") == token
    )


async def _finish(callback: CallbackQuery, text: str) -> None:
    """Убрать кнопки у вопроса плательщику и дописать итог."""
    if isinstance(callback.message, Message):
        await callback.message.edit_text(f"{callback.message.html_text}\n\n<i>{text}</i>")
