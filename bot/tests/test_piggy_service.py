from decimal import Decimal

import pytest

from obshak_bot.api import SavingsGoalDto
from obshak_bot.services import (
    AuthService,
    GroupService,
    PiggyBankService,
    TelegramUser,
    UserError,
    progress_line,
)
from obshak_bot.storage import ChatGroupRepository, Database, UserSessionRepository
from tests.fake_backend import FakeBackend

OWNER = TelegramUser(id=1, name="Owner")


@pytest.fixture
def services(db: Database) -> tuple[FakeBackend, GroupService, PiggyBankService]:
    backend = FakeBackend()
    api = backend.client()
    sessions = UserSessionRepository(db)
    auth = AuthService(api, sessions)
    return (
        backend,
        GroupService(api, auth, sessions, ChatGroupRepository(db)),
        PiggyBankService(api, auth),
    )


async def test_create_list_and_contribute(
    services: tuple[FakeBackend, GroupService, PiggyBankService],
) -> None:
    backend, groups, piggy = services
    group = await groups.create(OWNER, "Квартира")

    created = await piggy.create(OWNER, group.id, "На отпуск", Decimal("1000"))
    assert created.name == "На отпуск" and created.target_amount == Decimal("1000")
    assert created.type == "group" and created.current_amount == Decimal("0")

    listed = await piggy.list(OWNER, group.id)
    assert [g.name for g in listed] == ["На отпуск"]

    updated = await piggy.contribute(OWNER, created.id, Decimal("250"))
    assert updated.current_amount == Decimal("250")
    assert backend.contributions[0]["amount"] == 250.0


async def test_active_goal_rejects_missing_and_closed(
    services: tuple[FakeBackend, GroupService, PiggyBankService],
) -> None:
    backend, groups, piggy = services
    group = await groups.create(OWNER, "Квартира")
    goal = backend.add_goal(group.id, "Старая")
    goal["status"] = "completed"

    with pytest.raises(UserError, match="нет"):
        await piggy.active_goal(OWNER, group.id, "missing")
    with pytest.raises(UserError, match="закрыта"):
        await piggy.active_goal(OWNER, group.id, goal["id"])


def test_progress_line_shows_percent_and_bar() -> None:
    goal = SavingsGoalDto(
        id="g1",
        name="Отпуск",
        type="group",
        target_amount=Decimal("1000"),
        current_amount=Decimal("250"),
        status="active",
    )
    line = progress_line(goal)
    assert "Отпуск" in line and "250,00 ₽" in line and "(25%)" in line
    assert "██" in line and "░" in line
