from decimal import Decimal

from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage

from obshak_bot.handlers.expenses import ExpenseForm
from obshak_bot.handlers.payer_confirmation import is_pending_confirmation
from obshak_bot.services import AuthService, TelegramUser, payer_confirmation_request
from obshak_bot.storage import Database, UserSessionRepository
from tests.fake_backend import FakeBackend


def _fsm(storage: MemoryStorage, telegram_id: int) -> FSMContext:
    return FSMContext(
        storage=storage, key=StorageKey(bot_id=1, chat_id=telegram_id, user_id=telegram_id)
    )


async def test_pending_confirmation_accepts_only_matching_token() -> None:
    initiator = _fsm(MemoryStorage(), 100)
    await initiator.set_state(ExpenseForm.awaiting_payer)
    await initiator.update_data(confirm_token="abc")

    assert await is_pending_confirmation(initiator, "abc") is True
    assert await is_pending_confirmation(initiator, "other") is False

    await initiator.clear()
    assert await is_pending_confirmation(initiator, "abc") is False


def test_payer_confirmation_request_names_the_expense() -> None:
    text = payer_confirmation_request("Артём", "Квартира", Decimal("1250"), "Пицца", "Еда")
    assert "Артём" in text and "Квартира" in text
    assert "1 250,00 ₽" in text and "Пицца" in text and "Еда" in text
    assert "Подтверждаешь" in text


async def test_telegram_id_of_known_and_unknown_user(db: Database) -> None:
    backend = FakeBackend()
    service = AuthService(backend.client(), UserSessionRepository(db))
    user, _ = await service.login(TelegramUser(id=7, name="Друг"))

    assert await service.telegram_id_of(user.id) == 7
    assert await service.telegram_id_of("unknown") is None
