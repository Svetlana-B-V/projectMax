from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from obshak_bot.api import DebtDto, DebtUserDto
from obshak_bot.services import (
    AuthService,
    DebtService,
    ExpenseDraft,
    ExpenseService,
    GroupService,
    ReminderService,
    TelegramUser,
    render_debt_reminder,
)
from obshak_bot.services.reminders import _is_due
from obshak_bot.storage import ChatGroupRepository, Database, UserSessionRepository
from tests.fake_backend import FakeBackend

OWNER = TelegramUser(id=1, name="Owner")
FRIEND = TelegramUser(id=2, name="Friend")


def _debt(amount: str = "50.00") -> DebtDto:
    return DebtDto(
        id="d1",
        group_id="g1",
        from_user_id="u2",
        to_user_id="u1",
        amount=Decimal(amount),
        status="pending",
        to_user=DebtUserDto(id="u1", name="Owner"),
    )


def test_render_styles_mention_total_and_creditor() -> None:
    debts = [_debt()]
    assert "50,00 ₽" in render_debt_reminder("neutral", debts)
    assert "Привет" in render_debt_reminder("soft", debts)
    assert "Кошелёк" in render_debt_reminder("playful", debts)
    assert "Owner" in render_debt_reminder("neutral", debts)


def test_is_due_when_never_or_old() -> None:
    hour = timedelta(hours=1)
    assert _is_due(None, hour) is True
    old = (datetime.now(UTC) - timedelta(hours=2)).isoformat()
    fresh = datetime.now(UTC).isoformat()
    assert _is_due(old, hour) is True
    assert _is_due(fresh, hour) is False


@pytest.fixture
async def world(db: Database) -> dict:
    backend = FakeBackend()
    api = backend.client()
    sessions = UserSessionRepository(db)
    auth = AuthService(api, sessions)
    groups = GroupService(api, auth, sessions, ChatGroupRepository(db))
    expenses = ExpenseService(api, auth)
    debts = DebtService(api, auth)
    reminders = ReminderService(api, auth, debts, interval_hours=24)
    group = await groups.create(OWNER, "Квартира")
    await groups.join_by_code(FRIEND, group.invite_code)
    ids = {m.user.name: m.user_id for m in await groups.members(OWNER, group.id)}
    await expenses.create(
        OWNER, ExpenseDraft(group.id, ids["Owner"], Decimal("100"), (ids["Owner"], ids["Friend"]))
    )
    return {"backend": backend, "reminders": reminders}


async def test_due_text_when_user_owes(world: dict) -> None:
    reminders: ReminderService = world["reminders"]
    assert await reminders.due_text(OWNER) is None
    text = await reminders.due_text(FRIEND)
    assert text is not None and "50,00 ₽" in text and "Owner" in text

    await reminders.ack(FRIEND)
    assert await reminders.due_text(FRIEND) is None
    assert await reminders.due_text(FRIEND, force=True) is not None


async def test_disable_stops_reminders(world: dict) -> None:
    reminders: ReminderService = world["reminders"]
    await reminders.set_enabled(FRIEND, False)
    assert await reminders.due_text(FRIEND, force=True) is None
    settings = await reminders.set_style(FRIEND, "playful")
    assert settings.style == "playful"
    await reminders.set_enabled(FRIEND, True)
    assert "Кошелёк" in (await reminders.due_text(FRIEND, force=True) or "")
