from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.types import Message

from obshak_bot.keyboards import BTN_ACHIEVEMENTS
from obshak_bot.services import AchievementService, TelegramUser
from obshak_bot.services.achievements import format_board, format_unlocks

router = Router(name="achievements_private")
router.message.filter(F.chat.type == ChatType.PRIVATE)


@router.message(F.text == BTN_ACHIEVEMENTS)
async def show_achievements(message: Message, achievements: AchievementService) -> None:
    if message.from_user is None:
        return
    actor = TelegramUser.from_aiogram(message.from_user)
    fresh = await achievements.check(actor)
    if fresh:
        text = format_unlocks(fresh)
        if text:
            await message.answer(text)
    await message.answer(format_board(await achievements.list(actor)))
