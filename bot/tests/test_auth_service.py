from obshak_bot.services import AuthService, TelegramUser
from obshak_bot.storage import Database, UserSessionRepository
from tests.fake_backend import FakeBackend

ARTEM = TelegramUser(id=42, name="Артём")


async def test_login_registers_user_and_caches_session(db: Database) -> None:
    backend = FakeBackend()
    service = AuthService(backend.client(), UserSessionRepository(db))

    user, session = await service.login(ARTEM)

    assert backend.users[42]["name"] == "Артём"
    assert user.name == "Артём"
    assert user.telegram_id == 42
    assert session.access_token in backend.valid_tokens
    assert await service.ensure_session(ARTEM) == session
    assert backend.calls.count("POST /api/auth/telegram") == 1


async def test_run_authorized_relogins_on_401(db: Database) -> None:
    backend = FakeBackend()
    api = backend.client()
    service = AuthService(api, UserSessionRepository(db))
    await service.login(ARTEM)
    backend.revoke_all_tokens()

    groups = await service.run_authorized(ARTEM, api.my_groups)

    assert groups == []
    assert backend.calls.count("POST /api/auth/telegram") == 2
    assert backend.calls.count("GET /api/groups/my") == 2
