from __future__ import annotations

from obshak_bot.api import AchievementDto, ObshakApiClient
from obshak_bot.services.auth import AuthService, TelegramUser


class AchievementService:
    """Каталог достижений и проверка новых после действий пользователя."""

    def __init__(self, api: ObshakApiClient, auth: AuthService) -> None:
        self._api = api
        self._auth = auth

    async def list(self, actor: TelegramUser) -> list[AchievementDto]:
        return await self._auth.run_authorized(actor, self._api.achievements)

    async def check(self, actor: TelegramUser) -> list[AchievementDto]:
        """Открыть те, что уже заработаны, но ещё не записаны. Возвращает только новые."""
        return await self._auth.run_authorized(actor, self._api.check_achievements)


def format_unlocks(fresh: list[AchievementDto]) -> str | None:
    if not fresh:
        return None
    lines = [f"{a.icon or '🏆'} <b>{a.name}</b> — {a.description}" for a in fresh]
    title = "🎉 Новое достижение!" if len(fresh) == 1 else "🎉 Новые достижения!"
    return title + "\n" + "\n".join(lines)


def format_board(items: list[AchievementDto]) -> str:
    if not items:
        return "Пока нет достижений — бэкенд ещё не засеял каталог."
    done = [a for a in items if a.earned_at]
    lines = [f"Достижения: {len(done)} из {len(items)}", ""]
    for item in items:
        mark = "✅" if item.earned_at else "🔒"
        icon = item.icon or "🏆"
        lines.append(f"{mark} {icon} <b>{item.name}</b>\n    {item.description}")
    return "\n".join(lines)
