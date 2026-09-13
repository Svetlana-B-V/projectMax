import json

import httpx
import pytest

from obshak_bot.api import ApiError, ApiNotFound, ApiUnauthorized, ApiUnavailable, ObshakApiClient


def make_client(handler) -> ObshakApiClient:
    return ObshakApiClient(
        "http://backend.test",
        timeout_seconds=1,
        transport=httpx.MockTransport(handler),
    )


async def test_login_by_telegram_sends_numeric_id_and_name() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/auth/telegram"
        assert json.loads(request.content) == {"telegramId": 42, "name": "Артём"}
        return httpx.Response(
            200,
            json={
                "user": {"id": "u1", "email": None, "name": "Артём", "telegramId": "42"},
                "accessToken": "jwt",
            },
        )

    result = await make_client(handler).login_by_telegram(42, "Артём")

    assert result.access_token == "jwt"
    assert result.user.id == "u1"
    assert result.user.telegram_id == 42


async def test_404_raises_not_found_with_backend_message() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"message": "Группа не найдена"})

    with pytest.raises(ApiNotFound) as exc_info:
        await make_client(handler).join_group("t", "NOPE")
    assert exc_info.value.message == "Группа не найдена"


async def test_401_raises_unauthorized() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"message": "Сессия не найдена"})

    with pytest.raises(ApiUnauthorized):
        await make_client(handler).my_groups("stale")


async def test_other_errors_raise_api_error_with_status() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="boom")

    with pytest.raises(ApiError) as exc_info:
        await make_client(handler).my_groups("t")
    assert exc_info.value.status_code == 500


async def test_network_failure_raises_unavailable() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused")

    with pytest.raises(ApiUnavailable):
        await make_client(handler).my_groups("t")


async def test_bearer_token_is_sent() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer secret"
        return httpx.Response(200, json=[])

    assert await make_client(handler).my_groups("secret") == []
