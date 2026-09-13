from collections.abc import AsyncIterator

import pytest

from obshak_bot.storage import Database


@pytest.fixture
async def db() -> AsyncIterator[Database]:
    database = Database(":memory:")
    await database.connect()
    yield database
    await database.close()
