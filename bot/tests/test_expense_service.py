from decimal import Decimal

import pytest

from obshak_bot.api import ApiError
from obshak_bot.services import (
    AuthService,
    ExpenseDraft,
    ExpenseService,
    GroupService,
    TelegramUser,
    plan_shares,
)
from obshak_bot.storage import ChatGroupRepository, Database, UserSessionRepository
from tests.fake_backend import FakeBackend

OWNER = TelegramUser(id=1, name="Owner")
FRIEND = TelegramUser(id=2, name="Friend")
STRANGER = TelegramUser(id=3, name="Stranger")


@pytest.fixture
def backend() -> FakeBackend:
    return FakeBackend()


@pytest.fixture
def services(db: Database, backend: FakeBackend) -> tuple[GroupService, ExpenseService]:
    api = backend.client()
    sessions = UserSessionRepository(db)
    auth = AuthService(api, sessions)
    return GroupService(api, auth, sessions, ChatGroupRepository(db)), ExpenseService(api, auth)


async def _group_with_two_members(groups: GroupService) -> tuple[str, str, str]:
    group = await groups.create(OWNER, "Квартира")
    await groups.join_by_code(FRIEND, group.invite_code)
    members = {m.user.name: m.user_id for m in await groups.members(OWNER, group.id)}
    return group.id, members["Owner"], members["Friend"]


def test_plan_shares_equal_with_remainder() -> None:
    draft = ExpenseDraft("g", "a", Decimal("100"), ("a", "b", "c"))
    plan = plan_shares(draft)
    assert plan.shares == {"a": Decimal("33.33"), "b": Decimal("33.33"), "c": Decimal("33.33")}
    assert plan.remainder == Decimal("0.01")


def test_plan_shares_custom_must_match_total() -> None:
    ok = ExpenseDraft(
        "g", "a", Decimal("100"), ("a", "b"), custom_shares={"a": Decimal("70"), "b": Decimal("30")}
    )
    assert plan_shares(ok).shares == {"a": Decimal("70"), "b": Decimal("30")}
    assert plan_shares(ok).remainder == 0

    bad = ExpenseDraft(
        "g", "a", Decimal("100"), ("a", "b"), custom_shares={"a": Decimal("70"), "b": Decimal("20")}
    )
    with pytest.raises(ValueError):
        plan_shares(bad)


async def test_create_expense_sends_splits(
    services: tuple[GroupService, ExpenseService], backend: FakeBackend
) -> None:
    groups, expenses = services
    group_id, owner_id, friend_id = await _group_with_two_members(groups)
    category = await expenses.create_category(OWNER, group_id, "Еда")

    result = await expenses.create(
        OWNER,
        ExpenseDraft(
            group_id, owner_id, Decimal("100"), (owner_id, friend_id), category.id, "Пицца"
        ),
    )

    assert result.expense.amount == Decimal("100")
    assert result.plan.remainder == 0 and result.piggy_bank is None
    sent = backend.expenses[0]
    assert sent["payerId"] == owner_id and sent["categoryId"] == category.id
    assert sent["description"] == "Пицца"
    assert sorted(sent["splits"], key=lambda s: s["userId"]) == sorted(
        [{"userId": owner_id, "amountOwed": 50.0}, {"userId": friend_id, "amountOwed": 50.0}],
        key=lambda s: s["userId"],
    )
    assert [c.name for c in await expenses.categories(OWNER, group_id)] == ["Еда"]


async def test_remainder_goes_to_group_piggy_bank(
    services: tuple[GroupService, ExpenseService], backend: FakeBackend
) -> None:
    groups, expenses = services
    group_id, owner_id, friend_id = await _group_with_two_members(groups)
    backend.add_goal(group_id, "Личная", goal_type="personal")
    goal = backend.add_goal(group_id, "На отпуск")

    result = await expenses.create(
        OWNER, ExpenseDraft(group_id, owner_id, Decimal("100"), (owner_id, friend_id, "u-third"))
    )

    assert result.plan.remainder == Decimal("0.01")
    assert result.piggy_bank is not None and result.piggy_bank.id == goal["id"]
    assert backend.contributions == [{"goalId": goal["id"], "userId": owner_id, "amount": 0.01}]


async def test_remainder_stays_with_payer_without_piggy_bank(
    services: tuple[GroupService, ExpenseService], backend: FakeBackend
) -> None:
    groups, expenses = services
    group_id, owner_id, friend_id = await _group_with_two_members(groups)

    result = await expenses.create(
        OWNER, ExpenseDraft(group_id, owner_id, Decimal("100"), (owner_id, friend_id, "u-third"))
    )

    assert result.plan.remainder == Decimal("0.01")
    assert result.piggy_bank is None
    assert backend.contributions == []


async def test_stranger_cannot_add_expense(
    services: tuple[GroupService, ExpenseService],
) -> None:
    groups, expenses = services
    group_id, owner_id, _ = await _group_with_two_members(groups)
    with pytest.raises(ApiError) as exc_info:
        await expenses.create(
            STRANGER, ExpenseDraft(group_id, owner_id, Decimal("10"), (owner_id,))
        )
    assert exc_info.value.status_code == 403
