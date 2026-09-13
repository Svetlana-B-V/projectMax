import logging
from typing import Any

import httpx

from obshak_bot.api.schemas import (
    AchievementDto,
    AuthResult,
    CategoryDto,
    DebtDto,
    ExpenseCreate,
    ExpenseDto,
    GroupDto,
    GroupMemberDto,
    RecognizedReceiptDto,
    ReminderSettingsDto,
    SavingsGoalDto,
)

log = logging.getLogger(__name__)


class ApiError(Exception):
    """Бэкенд ответил ошибкой (4xx/5xx)."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(f"{status_code}: {message}")
        self.status_code = status_code
        self.message = message


class ApiNotFound(ApiError):
    """Ресурс не найден (404)."""

    def __init__(self, message: str) -> None:
        super().__init__(404, message)


class ApiUnauthorized(ApiError):
    """Токен недействителен или истёк (401)."""

    def __init__(self, message: str) -> None:
        super().__init__(401, message)


class ApiUnavailable(Exception):
    """Не удалось связаться с бэкендом (сеть, таймаут)."""


class ObshakApiClient:
    """HTTP-клиент к веб-бэкенду «Общака»."""

    def __init__(
        self,
        base_url: str,
        timeout_seconds: float,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._http = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=timeout_seconds,
            transport=transport,
        )

    async def aclose(self) -> None:
        await self._http.aclose()

    # --- auth ---

    async def login_by_telegram(self, telegram_id: int, name: str) -> AuthResult:
        """Вход по Telegram ID; бэкенд создаёт пользователя с этим именем, если его ещё нет."""
        data = await self._request(
            "POST", "/api/auth/telegram", json={"telegramId": telegram_id, "name": name}
        )
        return AuthResult.model_validate(data)

    # --- groups ---

    async def create_group(self, token: str, name: str) -> GroupDto:
        data = await self._request("POST", "/api/groups", token=token, json={"name": name})
        return GroupDto.model_validate(data)

    async def my_groups(self, token: str) -> list[GroupDto]:
        data = await self._request("GET", "/api/groups/my", token=token)
        return [GroupDto.model_validate(item) for item in data]

    async def join_group(self, token: str, invite_code: str) -> str:
        """Вступить в группу по коду. Возвращает id группы."""
        data = await self._request(
            "POST", "/api/groups/join", token=token, json={"inviteCode": invite_code}
        )
        return data["groupId"]

    async def group_members(self, token: str, group_id: str) -> list[GroupMemberDto]:
        data = await self._request("GET", f"/api/groups/{group_id}/members", token=token)
        return [GroupMemberDto.model_validate(item) for item in data]

    # --- categories ---

    async def categories(self, token: str, group_id: str) -> list[CategoryDto]:
        """Общие категории плюс категории группы."""
        data = await self._request(
            "GET", "/api/categories", token=token, params={"groupId": group_id}
        )
        return [CategoryDto.model_validate(item) for item in data]

    async def create_category(self, token: str, group_id: str, name: str) -> CategoryDto:
        data = await self._request(
            "POST", "/api/categories", token=token, json={"groupId": group_id, "name": name}
        )
        return CategoryDto.model_validate(data)

    # --- savings goals (копилки) ---

    async def create_savings_goal(
        self, token: str, group_id: str, name: str, target_amount: float
    ) -> SavingsGoalDto:
        data = await self._request(
            "POST",
            "/api/savings-goals",
            token=token,
            json={
                "groupId": group_id,
                "name": name,
                "type": "group",
                "targetAmount": target_amount,
            },
        )
        return SavingsGoalDto.model_validate(data)

    async def savings_goals(self, token: str, group_id: str) -> list[SavingsGoalDto]:
        data = await self._request("GET", f"/api/savings-goals/group/{group_id}", token=token)
        return [SavingsGoalDto.model_validate(item) for item in data]

    async def contribute(
        self, token: str, goal_id: str, amount: float, note: str | None = None
    ) -> SavingsGoalDto:
        body: dict[str, Any] = {"amount": amount}
        if note:
            body["note"] = note
        data = await self._request(
            "POST", f"/api/savings-goals/{goal_id}/contribute", token=token, json=body
        )
        return SavingsGoalDto.model_validate(data)

    # --- debts ---

    async def group_debts(self, token: str, group_id: str) -> list[DebtDto]:
        """Непогашенные долги группы."""
        data = await self._request("GET", f"/api/debts/group/{group_id}", token=token)
        return [DebtDto.model_validate(item) for item in data]

    async def pay_debt(self, token: str, debt_id: str, amount: float) -> DebtDto:
        data = await self._request(
            "POST", f"/api/debts/{debt_id}/pay", token=token, json={"amount": amount}
        )
        return DebtDto.model_validate(data)

    # --- expenses ---

    async def my_debts(self, token: str) -> list[DebtDto]:
        data = await self._request("GET", "/api/debts/my", token=token)
        return [DebtDto.model_validate(item) for item in data]

    async def upload_receipt(self, token: str, image: bytes) -> RecognizedReceiptDto:
        data = await self._request(
            "POST",
            "/api/expenses/receipt",
            token=token,
            files={"photo": ("receipt.jpg", image, "image/jpeg")},
        )
        return RecognizedReceiptDto.model_validate(data)

    async def reminder_settings(self, token: str) -> ReminderSettingsDto:
        data = await self._request("GET", "/api/reminders", token=token)
        return ReminderSettingsDto.model_validate(data)

    async def update_reminder_settings(
        self, token: str, *, style: str | None = None, enabled: bool | None = None
    ) -> ReminderSettingsDto:
        body: dict[str, Any] = {}
        if style is not None:
            body["style"] = style
        if enabled is not None:
            body["enabled"] = enabled
        data = await self._request("PUT", "/api/reminders", token=token, json=body)
        return ReminderSettingsDto.model_validate(data)

    async def achievements(self, token: str) -> list[AchievementDto]:
        data = await self._request("GET", "/api/achievements", token=token)
        return [AchievementDto.model_validate(item) for item in data]

    async def check_achievements(self, token: str) -> list[AchievementDto]:
        data = await self._request("POST", "/api/achievements/check", token=token)
        return [AchievementDto.model_validate(item) for item in data]

    async def ack_reminder(self, token: str) -> ReminderSettingsDto:
        data = await self._request("POST", "/api/reminders/ack", token=token)
        return ReminderSettingsDto.model_validate(data)

    async def create_expense(self, token: str, payload: ExpenseCreate) -> ExpenseDto:
        data = await self._request(
            "POST",
            "/api/expenses",
            token=token,
            json=payload.model_dump(by_alias=True, exclude_none=True),
        )
        return ExpenseDto.model_validate(data)

    # --- internals ---

    async def _request(
        self,
        method: str,
        path: str,
        *,
        token: str | None = None,
        **kwargs: Any,
    ) -> Any:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        try:
            response = await self._http.request(method, path, headers=headers, **kwargs)
        except httpx.HTTPError as exc:
            log.warning("Backend unreachable: %s %s (%s)", method, path, type(exc).__name__)
            raise ApiUnavailable(str(exc)) from exc

        if response.is_success:
            return response.json() if response.content else None

        message = _error_message(response)
        log.info("Backend error: %s %s -> %s %s", method, path, response.status_code, message)
        if response.status_code == 404:
            raise ApiNotFound(message)
        if response.status_code == 401:
            raise ApiUnauthorized(message)
        raise ApiError(response.status_code, message)


def _error_message(response: httpx.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        return response.reason_phrase
    if isinstance(body, dict) and isinstance(body.get("message"), str):
        return body["message"]
    return response.reason_phrase
