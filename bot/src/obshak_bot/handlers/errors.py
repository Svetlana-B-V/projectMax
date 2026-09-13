import logging

from aiogram import Bot, Router
from aiogram.filters import ExceptionTypeFilter
from aiogram.types import ErrorEvent, Update

from obshak_bot.api import ApiError, ApiUnavailable
from obshak_bot.services import UserError

log = logging.getLogger(__name__)

router = Router(name="errors")


@router.errors(ExceptionTypeFilter(UserError))
async def on_user_error(event: ErrorEvent, bot: Bot) -> None:
    assert isinstance(event.exception, UserError)
    await _reply(bot, event.update, event.exception.message)


@router.errors(ExceptionTypeFilter(ApiUnavailable))
async def on_backend_unavailable(event: ErrorEvent, bot: Bot) -> None:
    await _reply(bot, event.update, "Сервер «Общака» сейчас недоступен. Попробуй через минуту.")


@router.errors(ExceptionTypeFilter(ApiError))
async def on_api_error(event: ErrorEvent, bot: Bot) -> None:
    assert isinstance(event.exception, ApiError)
    await _reply(bot, event.update, f"Не получилось: {event.exception.message}")


@router.errors()
async def on_unexpected(event: ErrorEvent, bot: Bot) -> None:
    log.exception("Unhandled error on update %s", event.update.update_id, exc_info=event.exception)
    await _reply(bot, event.update, "Что-то пошло не так. Попробуй ещё раз.")


async def _reply(bot: Bot, update: Update, text: str) -> None:
    if update.callback_query is not None:
        await update.callback_query.answer()
        chat_id = update.callback_query.message.chat.id if update.callback_query.message else None
    elif update.message is not None:
        chat_id = update.message.chat.id
    elif update.my_chat_member is not None:
        chat_id = update.my_chat_member.chat.id
    else:
        return
    if chat_id is not None:
        await bot.send_message(chat_id, text)
