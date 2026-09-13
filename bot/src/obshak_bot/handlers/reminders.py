"""Настройки напоминаний о долгах: стиль и вкл/выкл."""

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.types import CallbackQuery, Message

from obshak_bot.api import ReminderSettingsDto
from obshak_bot.keyboards import BTN_REMINDERS, ReminderCb, reminders_menu
from obshak_bot.services import Notifier, ReminderService, TelegramUser
from obshak_bot.services.reminders import STYLE_LABELS

router = Router(name="reminders")
router.message.filter(F.chat.type == ChatType.PRIVATE)
router.callback_query.filter(F.message.chat.type == ChatType.PRIVATE)


@router.message(F.text == BTN_REMINDERS)
async def show_reminders(message: Message, reminders: ReminderService, notifier: Notifier) -> None:
    if message.from_user is None:
        return
    actor = TelegramUser.from_aiogram(message.from_user)
    settings = await reminders.settings(actor)
    await message.answer(
        _text(settings), reply_markup=reminders_menu(settings.enabled, settings.style)
    )
    await _maybe_send_now(actor, reminders, notifier, force=False)


@router.callback_query(ReminderCb.filter(F.action == "style"))
async def set_style(
    callback: CallbackQuery, callback_data: ReminderCb, reminders: ReminderService
) -> None:
    actor = TelegramUser.from_aiogram(callback.from_user)
    settings = await reminders.set_style(actor, callback_data.value)
    await callback.answer(f"Стиль: {STYLE_LABELS[settings.style]}")
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            _text(settings), reply_markup=reminders_menu(settings.enabled, settings.style)
        )


@router.callback_query(ReminderCb.filter(F.action == "toggle"))
async def toggle(callback: CallbackQuery, reminders: ReminderService, notifier: Notifier) -> None:
    actor = TelegramUser.from_aiogram(callback.from_user)
    current = await reminders.settings(actor)
    settings = await reminders.set_enabled(actor, not current.enabled)
    await callback.answer("Включены" if settings.enabled else "Выключены")
    if isinstance(callback.message, Message):
        await callback.message.edit_text(
            _text(settings), reply_markup=reminders_menu(settings.enabled, settings.style)
        )
    if settings.enabled:
        await _maybe_send_now(actor, reminders, notifier, force=True)


async def _maybe_send_now(
    actor: TelegramUser, reminders: ReminderService, notifier: Notifier, *, force: bool
) -> None:
    text = await reminders.due_text(actor, force=force)
    if text is None:
        return
    if await notifier.send(actor.id, text):
        await reminders.ack(actor)


def _text(settings: ReminderSettingsDto) -> str:
    status = "включены" if settings.enabled else "выключены"
    style = STYLE_LABELS.get(settings.style, settings.style)
    return (
        f"Напоминания о долгах: <b>{status}</b>, стиль «{style}».\n"
        "Если есть незакрытые долги, бот напишет в личку (не чаще раза в сутки)."
    )
