import pytest

from obshak_bot.services import AuthService, GroupService, TelegramUser, UserError
from obshak_bot.storage import ChatGroupRepository, Database, UserSessionRepository
from tests.fake_backend import FakeBackend

OWNER = TelegramUser(id=1, name="Owner")
FRIEND = TelegramUser(id=2, name="Friend")


@pytest.fixture
def backend() -> FakeBackend:
    return FakeBackend()


@pytest.fixture
def service(db: Database, backend: FakeBackend) -> GroupService:
    api = backend.client()
    sessions = UserSessionRepository(db)
    return GroupService(api, AuthService(api, sessions), sessions, ChatGroupRepository(db))


async def test_first_created_group_becomes_current(service: GroupService) -> None:
    first = await service.create(OWNER, "Семья")
    second = await service.create(OWNER, "Друзья")

    current = await service.current(OWNER)
    assert current is not None and current.id == first.id
    assert {g.name for g in await service.list_my(OWNER)} == {"Семья", "Друзья"}

    await service.select_current(OWNER, second.id)
    assert (await service.current(OWNER)).id == second.id


async def test_select_foreign_group_is_rejected(service: GroupService) -> None:
    group = await service.create(OWNER, "Семья")
    with pytest.raises(UserError):
        await service.select_current(FRIEND, group.id)


async def test_join_by_code_and_members(service: GroupService) -> None:
    group = await service.create(OWNER, "Семья")

    joined = await service.join_by_code(FRIEND, group.invite_code)

    assert joined.id == group.id
    assert (await service.current(FRIEND)).id == group.id
    members = await service.members(OWNER, group.id)
    assert {(m.user.name, m.role) for m in members} == {("Owner", "owner"), ("Friend", "member")}


async def test_bind_chat_and_auto_join(service: GroupService) -> None:
    group = await service.bind_chat(-100, owner=OWNER, title="Квартира")
    binding = await service.chat_binding(-100)
    assert binding is not None and binding.group_id == group.id

    assert await service.join_chat_group(FRIEND, binding) is True  # вступил
    assert await service.join_chat_group(FRIEND, binding) is False  # уже в кэше
    assert await service.join_chat_group(OWNER, binding) is False  # владелец

    names = {m.user.name for m in await service.members(OWNER, group.id)}
    assert names == {"Owner", "Friend"}

    await service.unbind_chat(-100)
    assert await service.chat_binding(-100) is None


async def test_join_chat_group_when_backend_says_already_member(service: GroupService) -> None:
    group = await service.bind_chat(-100, owner=OWNER, title="Квартира")
    await service.join_by_code(FRIEND, group.invite_code)  # вступил вручную, кэш чата пуст

    binding = await service.chat_binding(-100)
    assert await service.join_chat_group(FRIEND, binding) is False
