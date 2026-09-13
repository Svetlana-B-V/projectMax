from decimal import Decimal

import pytest

from obshak_bot.api import AchievementDto
from obshak_bot.services import (
    AchievementService,
    AuthService,
    DebtService,
    ExpenseDraft,
    ExpenseService,
    GroupService,
    PiggyBankService,
    TelegramUser,
    format_board,
    format_unlocks,
)
from obshak_bot.storage import ChatGroupRepository, Database, UserSessionRepository
from tests.fake_backend import FakeBackend

OWNER = TelegramUser(id=1, name="Owner")
FRIEND = TelegramUser(id=2, name="Friend")

Services = tuple[
    GroupService, ExpenseService, AchievementService, DebtService, PiggyBankService
]


@pytest.fixture
def services(db: Database) -> Services:
    api = FakeBackend().client()
    sessions = UserSessionRepository(db)
    auth = AuthService(api, sessions)
    groups = GroupService(api, auth, sessions, ChatGroupRepository(db))
    return (
        groups,
        ExpenseService(api, auth),
        AchievementService(api, auth),
        DebtService(api, auth),
        PiggyBankService(api, auth),
    )


def test_format_board_and_unlocks() -> None:
    items = [
        AchievementDto(code="a", name="Первый шаг", description="Добавь расход", icon="🧾"),
        AchievementDto(
            code="b", name="Бухгалтер", description="3 расхода", icon="📊", earned_at="now"
        ),
    ]
    board = format_board(items)
    assert "1 из 2" in board and "🔒" in board and "✅" in board
    assert format_unlocks([]) is None
    assert "Новое достижение" in (format_unlocks(items[:1]) or "")


async def test_create_group_and_expense_unlocks(services: Services) -> None:
    groups, expenses, achievements, _, _ = services
    assert await achievements.check(OWNER) == []

    group = await groups.create(OWNER, "Квартира")
    assert {a.code for a in await achievements.check(OWNER)} == {"first_group"}
    assert await achievements.check(OWNER) == []

    ids = {m.user.name: m.user_id for m in await groups.members(OWNER, group.id)}
    await expenses.create(
        OWNER, ExpenseDraft(group.id, ids["Owner"], Decimal("10"), (ids["Owner"],))
    )
    assert {a.code for a in await achievements.check(OWNER)} == {"first_expense"}

    earned = {a.code for a in await achievements.list(OWNER) if a.earned_at}
    assert earned == {"first_group", "first_expense"}


async def test_three_expenses_and_squirrel(services: Services) -> None:
    groups, expenses, achievements, _, piggy = services
    group = await groups.create(OWNER, "Квартира")
    owner_id = next(
        m.user_id for m in await groups.members(OWNER, group.id) if m.user.name == "Owner"
    )
    for _ in range(3):
        await expenses.create(OWNER, ExpenseDraft(group.id, owner_id, Decimal("10"), (owner_id,)))
    assert {a.code for a in await achievements.check(OWNER)} == {
        "first_group",
        "first_expense",
        "three_expenses",
    }

    goal = await piggy.create(OWNER, group.id, "Отпуск", Decimal("1000"))
    await piggy.contribute(OWNER, goal.id, Decimal("100"))
    assert {a.code for a in await achievements.check(OWNER)} == {"first_contribute"}


async def test_payment_unlocks_honest_debtor(services: Services) -> None:
    groups, expenses, achievements, debts, _ = services
    group = await groups.create(OWNER, "Квартира")
    await groups.join_by_code(FRIEND, group.invite_code)
    ids = {m.user.name: m.user_id for m in await groups.members(OWNER, group.id)}
    await expenses.create(
        OWNER, ExpenseDraft(group.id, ids["Owner"], Decimal("100"), (ids["Owner"], ids["Friend"]))
    )
    await achievements.check(OWNER)
    debt_id = (await debts.overview(FRIEND, group.id)).i_owe[0].id
    await debts.pay(FRIEND, group.id, debt_id, None)

    assert {a.code for a in await achievements.check(FRIEND)} == {"first_payment"}
