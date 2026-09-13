import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Update

from obshak_bot.storage import ProcessedUpdateRepository

log = logging.getLogger(__name__)


class DedupUpdateMiddleware(BaseMiddleware):
    """Пропускает update, который уже обрабатывался (защита от дублей после перезапуска/сбоев)."""

    def __init__(self, processed_updates: ProcessedUpdateRepository) -> None:
        self._processed_updates = processed_updates

    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any],
    ) -> Any:
        if not await self._processed_updates.try_mark(event.update_id):
            log.info("Duplicate update %s skipped", event.update_id)
            return None
        return await handler(event, data)
