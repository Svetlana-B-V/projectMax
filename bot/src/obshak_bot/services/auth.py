from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from aiogram.types import User as AiogramUser

from obshak_bot.api import ApiUnauthorized, ObshakApiClient, UserDto
from obshak_bot.storage import UserSession, UserSessionRepository


@dataclass(frozen=True, slots=True)
class TelegramUser:
    """Кто действует: Telegram ID и отображаемое имя (нужно бэкенду при первом входе)."""

    id: int
    name: str

    @classmethod
    def from_aiogram(cls, user: AiogramUser) -> "TelegramUser":
        return cls(id=user.id, name=user.full_name)


class AuthService:
    """Вход (и регистрация) пользователя Telegram в бэкенде, кэш его сессии."""

    def __init__(self, api: ObshakApiClient, sessions: UserSessionRepository) -> None:
        self._api = api
        self._sessions = sessions

    async def login(self, actor: TelegramUser) -> tuple[UserDto, UserSession]:
        """Войти через бэкенд (он создаёт пользователя, если его нет) и сохранить токен."""
        auth = await self._api.login_by_telegram(actor.id, actor.name)
        await self._sessions.save_login(actor.id, auth.user.id, auth.access_token)
        session = await self._sessions.get(actor.id)
        assert session is not None
        return auth.user, session

    async def ensure_session(self, actor: TelegramUser) -> UserSession:
        """Вернуть кэшированную сессию или войти."""
        session = await self._sessions.get(actor.id)
        if session is None:
            _, session = await self.login(actor)
        return session

    async def telegram_id_of(self, user_id: str) -> int | None:
        """Telegram ID пользователя бэкенда, если он хоть раз заходил через бота."""
        return (await self._sessions.telegram_ids([user_id])).get(user_id)

    async def run_authorized[T](
        self, actor: TelegramUser, operation: Callable[[str], Awaitable[T]]
    ) -> T:
        """Выполнить запрос с токеном пользователя; при 401 — перелогиниться и повторить."""
        session = await self.ensure_session(actor)
        try:
            return await operation(session.access_token)
        except ApiUnauthorized:
            _, session = await self.login(actor)
            return await operation(session.access_token)
