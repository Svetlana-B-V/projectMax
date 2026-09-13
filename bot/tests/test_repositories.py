from obshak_bot.storage import (
    ChatGroupRepository,
    Database,
    ProcessedUpdateRepository,
    UserSessionRepository,
)


async def test_session_login_then_group_selection(db: Database) -> None:
    repo = UserSessionRepository(db)
    assert await repo.get(1) is None

    await repo.save_login(1, user_id="u1", access_token="t1")
    session = await repo.get(1)
    assert session is not None
    assert (session.user_id, session.access_token, session.current_group_id) == ("u1", "t1", None)

    await repo.set_current_group(1, "g1")
    assert (await repo.get(1)).current_group_id == "g1"


async def test_relogin_refreshes_token_but_keeps_current_group(db: Database) -> None:
    repo = UserSessionRepository(db)
    await repo.save_login(1, user_id="u1", access_token="t1")
    await repo.set_current_group(1, "g1")

    await repo.save_login(1, user_id="u1", access_token="t2")

    session = await repo.get(1)
    assert session.access_token == "t2"
    assert session.current_group_id == "g1"


async def test_session_delete(db: Database) -> None:
    repo = UserSessionRepository(db)
    await repo.save_login(1, user_id="u1", access_token="t1")
    await repo.delete(1)
    assert await repo.get(1) is None


async def test_telegram_ids_by_user_ids(db: Database) -> None:
    repo = UserSessionRepository(db)
    await repo.save_login(1, user_id="u1", access_token="t1")
    await repo.save_login(2, user_id="u2", access_token="t2")

    assert await repo.telegram_ids(["u1", "u2", "u-unknown"]) == {"u1": 1, "u2": 2}
    assert await repo.telegram_ids([]) == {}
    assert {s.telegram_id for s in await repo.list_all()} == {1, 2}


async def test_chat_group_find_by_group(db: Database) -> None:
    repo = ChatGroupRepository(db)
    await repo.bind(-100, "g1", "CODE1")

    assert (await repo.find_by_group("g1")).chat_id == -100
    assert await repo.find_by_group("g2") is None


async def test_chat_group_bind_rebind_unbind(db: Database) -> None:
    repo = ChatGroupRepository(db)
    assert await repo.get(-100) is None

    await repo.bind(-100, "g1", "CODE1")
    binding = await repo.get(-100)
    assert (binding.group_id, binding.invite_code) == ("g1", "CODE1")

    await repo.bind(-100, "g2", "CODE2")
    assert (await repo.get(-100)).group_id == "g2"

    await repo.unbind(-100)
    assert await repo.get(-100) is None


async def test_chat_members_cache_reset_on_rebind(db: Database) -> None:
    repo = ChatGroupRepository(db)
    await repo.bind(-100, "g1", "CODE1")
    await repo.add_member(-100, 1)
    assert await repo.is_member(-100, 1) is True
    assert await repo.is_member(-100, 2) is False

    await repo.bind(-100, "g2", "CODE2")
    assert await repo.is_member(-100, 1) is False


async def test_processed_updates_mark_once(db: Database) -> None:
    repo = ProcessedUpdateRepository(db)
    assert await repo.try_mark(10) is True
    assert await repo.try_mark(10) is False
    assert await repo.try_mark(11) is True


async def test_processed_updates_purge_keeps_recent(db: Database) -> None:
    repo = ProcessedUpdateRepository(db)
    await repo.try_mark(1)
    await db.conn.execute(
        "UPDATE processed_updates SET processed_at = datetime('now', '-10 days') "
        "WHERE update_id = 1"
    )
    await repo.try_mark(2)

    assert await repo.purge_older_than(7) == 1
    assert await repo.try_mark(1) is True
    assert await repo.try_mark(2) is False
