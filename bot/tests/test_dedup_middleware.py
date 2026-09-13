from typing import Any

from aiogram.types import Update

from obshak_bot.middlewares import DedupUpdateMiddleware
from obshak_bot.storage import Database, ProcessedUpdateRepository


async def test_same_update_is_handled_once(db: Database) -> None:
    middleware = DedupUpdateMiddleware(ProcessedUpdateRepository(db))
    handled: list[int] = []

    async def handler(event: Update, data: dict[str, Any]) -> str:
        handled.append(event.update_id)
        return "ok"

    update = Update(update_id=7)
    assert await middleware(handler, update, {}) == "ok"
    assert await middleware(handler, update, {}) is None
    assert await middleware(handler, Update(update_id=8), {}) == "ok"

    assert handled == [7, 8]
