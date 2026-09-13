"""Список достижений и объявление новых после действий."""

from aiogram.types import ChatMemberUpdated, Message

from obshak_bot.services import AchievementService, TelegramUser
from obshak_bot.services.achievements import format_unlocks


async def announce_unlocks(
    target: Message | ChatMemberUpdated, actor: TelegramUser, achievements: AchievementService
) -> None:
    text = format_unlocks(await achievements.check(actor))
    if text:
        await target.answer(text)
