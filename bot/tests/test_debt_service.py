from decimal import Decimal

import pytest

from obshak_bot.services import (
    AuthService,
    DebtService,
    ExpenseDraft,
    ExpenseService,
    GroupService,
    TelegramUser,
    UserError,
    payment_summary,
)
from obshak_bot.storage import ChatGroupRepository, Database, UserSessionRepository
from tests.fake_backend import FakeBackend

OWNER = TelegramUser(id=1, name="Owner")
FRIEND = TelegramUser(id=2, name="Friend")


@pytest.fixture
def backend() -> FakeBackend:
    return FakeBackend()


@pytest.fixture
async def world(db: Database, backend: FakeBackend) -> dict:
    """Группа из двух человек, где Owner заплатил 100 за обоих: Friend должен 50."""
    api = backend.client()
    sessions = UserSessionRepository(db)
    auth = AuthService(api, sessions)
    groups = GroupService(api, auth, sessions, ChatGroupRepository(db))
    expenses = ExpenseService(api, auth)
    debts = DebtService(api, auth)

    group = await groups.create(OWNER, "Квартира")
    await groups.join_by_code(FRIEND, group.invite_code)
    ids = {m.user.name: m.user_id for m in await groups.members(OWNER, group.id)}
    await expenses.create(
        OWNER, ExpenseDraft(group.id, ids["Owner"], Decimal("100"), (ids["Owner"], ids["Friend"]))
    )
    return {"group_id": group.id, "debts": debts, "ids": ids}


async def test_overview_splits_debts_by_direction(world: dict) -> None:
    debts: DebtService = world["debts"]

    friend_view = await debts.overview(FRIEND, world["group_id"])
    owner_view = await debts.overview(OWNER, world["group_id"])

    assert [d.amount for d in friend_view.i_owe] == [Decimal("50")]
    assert friend_view.i_owe[0].to_user.name == "Owner"
    assert friend_view.i_owe[0].to_user.telegram_id == 1
    assert friend_view.owed_to_me == []
    assert [d.amount for d in owner_view.owed_to_me] == [Decimal("50")]
    assert owner_view.i_owe == []


async def test_partial_then_full_payment(world: dict, backend: FakeBackend) -> None:
    debts: DebtService = world["debts"]
    debt_id = (await debts.overview(FRIEND, world["group_id"])).i_owe[0].id

    partial = await debts.pay(FRIEND, world["group_id"], debt_id, Decimal("20"))
    assert (partial.amount, partial.remaining, partial.settled) == (
        Decimal("20"),
        Decimal("30"),
        False,
    )
    assert payment_summary(partial) == "Возврат 20,00 ₽. Осталось вернуть 30,00 ₽."

    full = await debts.pay(FRIEND, world["group_id"], debt_id, None)
    assert (full.amount, full.remaining, full.settled) == (Decimal("30"), Decimal("0"), True)
    assert payment_summary(full) == "Возврат 30,00 ₽. Долг закрыт ✅"

    friend_id = world["ids"]["Friend"]
    assert backend.payments == [
        {"debtId": debt_id, "amount": 20.0, "fromUserId": friend_id},
        {"debtId": debt_id, "amount": 30.0, "fromUserId": friend_id},
    ]
    assert (await debts.overview(FRIEND, world["group_id"])).is_empty


async def test_cannot_pay_someone_elses_debt(world: dict) -> None:
    debts: DebtService = world["debts"]
    debt_id = (await debts.overview(FRIEND, world["group_id"])).i_owe[0].id

    with pytest.raises(UserError):
        await debts.pay(OWNER, world["group_id"], debt_id, None)


async def test_cannot_overpay(world: dict) -> None:
    debts: DebtService = world["debts"]
    debt_id = (await debts.overview(FRIEND, world["group_id"])).i_owe[0].id

    with pytest.raises(UserError, match="50,00"):
        await debts.pay(FRIEND, world["group_id"], debt_id, Decimal("50.01"))
