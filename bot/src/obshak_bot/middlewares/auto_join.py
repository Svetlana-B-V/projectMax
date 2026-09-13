import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.enums import ChatType
from aiogram.types import Message

from obshak_bot.api import ApiError, ApiUnavailable
from obshak_bot.services import GroupService, TelegramUser

log = logging.getLogger(__name__)


class AutoJoinMiddleware(BaseMiddleware):
    """В привязанном групповом чате любой написавший автоматически вступает в группу «Общака»."""

    def __init__(self, groups: GroupService) -> None:
        self._groups = groups

    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        if event.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP) and event.from_user:
            await self._try_join(event)
        return await handler(event, data)

    async def _try_join(self, message: Message) -> None:
        assert message.from_user is not None
        binding = await self._groups.chat_binding(message.chat.id)
        if binding is None:
            return
        actor = TelegramUser.from_aiogram(message.from_user)
        try:
            joined = await self._groups.join_chat_group(actor, binding)
        except (ApiError, ApiUnavailable) as exc:
            log.warning("Auto-join failed for %s: %s", actor.id, exc)
            return
        if joined:
            await message.answer(f"{actor.name} теперь в группе.")
