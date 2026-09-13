from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.filters import (
    JOIN_TRANSITION,
    LEAVE_TRANSITION,
    ChatMemberUpdatedFilter,
    Command,
    CommandStart,
)
from aiogram.types import ChatMemberUpdated, Message

from obshak_bot.handlers.achievements import announce_unlocks
from obshak_bot.services import AchievementService, GroupService, TelegramUser

router = Router(name="group_chat")
_GROUP_TYPES = {ChatType.GROUP, ChatType.SUPERGROUP}
router.message.filter(F.chat.type.in_(_GROUP_TYPES))
router.my_chat_member.filter(F.chat.type.in_(_GROUP_TYPES))

_DEFAULT_TITLE = "Общая группа"


@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=JOIN_TRANSITION))
async def bot_added(
    event: ChatMemberUpdated, groups: GroupService, achievements: AchievementService
) -> None:
    await _bind_and_report(
        event, TelegramUser.from_aiogram(event.from_user), groups, achievements
    )


@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=LEAVE_TRANSITION))
async def bot_removed(event: ChatMemberUpdated, groups: GroupService) -> None:
    await groups.unbind_chat(event.chat.id)


@router.message(CommandStart())
@router.message(Command("join"))
async def join_chat_group(
    message: Message, groups: GroupService, achievements: AchievementService
) -> None:
    if message.from_user is None:
        return
    actor = TelegramUser.from_aiogram(message.from_user)
    binding = await groups.chat_binding(message.chat.id)
    if binding is None:
        await _bind_and_report(message, actor, groups, achievements)
        return
    joined = await groups.join_chat_group(actor, binding)
    if joined:
        await message.answer(f"{actor.name} теперь в группе.")
    else:
        await message.answer(f"{actor.name}, ты уже в группе.")


async def _bind_and_report(
    event: ChatMemberUpdated | Message,
    owner: TelegramUser,
    groups: GroupService,
    achievements: AchievementService,
) -> None:
    group = await groups.bind_chat(event.chat.id, owner, event.chat.title or _DEFAULT_TITLE)
    await event.answer(
        f"Чат привязан к группе «{group.name}» в «Общаке».\n"
        "Все, кто напишет в чат или нажмёт /join, автоматически станут её участниками."
    )
    await announce_unlocks(event, owner, achievements)
