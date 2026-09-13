"""Мини-заглушка бэкенда «Общака» для тестов сервисов (поверх httpx.MockTransport)."""

import json
from itertools import count

import httpx

from obshak_bot.api import ObshakApiClient

_ACHIEVEMENTS = [
    {
        "code": "first_expense",
        "name": "Первый шаг",
        "description": "Добавь первый расход",
        "icon": "🧾",
    },
    {
        "code": "three_expenses",
        "name": "Бухгалтер",
        "description": "Добавь 3 расхода",
        "icon": "📊",
    },
    {
        "code": "first_payment",
        "name": "Честный должник",
        "description": "Верни долг хотя бы раз",
        "icon": "🤝",
    },
    {
        "code": "first_contribute",
        "name": "Белочка",
        "description": "Положи деньги в копилку",
        "icon": "🐿️",
    },
    {
        "code": "first_group",
        "name": "Хозяин",
        "description": "Создай группу",
        "icon": "🏠",
    },
]


class FakeBackend:
    def __init__(self) -> None:
        self.users: dict[int, dict] = {}  # telegramId -> user
        self.groups: dict[str, dict] = {}  # groupId -> group
        self.members: dict[str, set[str]] = {}  # groupId -> userIds
        self.categories: list[dict] = []
        self.goals: list[dict] = []
        self.contributions: list[dict] = []
        self.expenses: list[dict] = []
        self.debts: list[dict] = []
        self.payments: list[dict] = []
        self.valid_tokens: set[str] = set()
        self.receipt_broken = False
        self.reminders: dict[str, dict] = {}
        self.unlocked: dict[str, set[str]] = {}
        self.calls: list[str] = []
        self._ids = count(1)

    def add_user(self, telegram_id: int, name: str) -> str:
        user_id = f"u{next(self._ids)}"
        self.users[telegram_id] = {"id": user_id, "name": name, "telegramId": str(telegram_id)}
        return user_id

    def revoke_all_tokens(self) -> None:
        self.valid_tokens.clear()

    def add_goal(
        self, group_id: str, name: str, goal_type: str = "group", target: float = 1000
    ) -> dict:
        goal = {
            "id": f"sg{next(self._ids)}",
            "groupId": group_id,
            "name": name,
            "type": goal_type,
            "targetAmount": f"{float(target):.2f}",
            "currentAmount": "0.00",
            "status": "active",
        }
        self.goals.append(goal)
        return goal

    def client(self) -> ObshakApiClient:
        return ObshakApiClient(
            "http://backend.test", timeout_seconds=1, transport=httpx.MockTransport(self._handle)
        )

    # --- routing ---

    def _handle(self, request: httpx.Request) -> httpx.Response:
        self.calls.append(f"{request.method} {request.url.path}")
        path = request.url.path
        try:
            body = json.loads(request.content) if request.content else {}
        except json.JSONDecodeError:
            body = {}

        if path == "/api/auth/telegram":
            telegram_id = body["telegramId"]
            if not isinstance(telegram_id, int):
                return httpx.Response(400, json={"message": "Ошибка валидации"})
            if telegram_id not in self.users:
                self.add_user(telegram_id, body.get("name") or "Пользователь")
            user = self.users[telegram_id]
            token = f"token-{user['id']}-{next(self._ids)}"
            self.valid_tokens.add(token)
            return httpx.Response(200, json={"user": user, "accessToken": token})

        user_id = self._authorize(request)
        if user_id is None:
            return httpx.Response(401, json={"message": "Недействительный токен"})

        if path == "/api/groups" and request.method == "POST":
            group_id = f"g{next(self._ids)}"
            group = {
                "id": group_id,
                "name": body["name"],
                "currency": "RUB",
                "inviteCode": f"CODE{group_id.upper()}",
                "ownerId": user_id,
            }
            self.groups[group_id] = group
            self.members[group_id] = {user_id}
            return httpx.Response(201, json=group)

        if path == "/api/groups/my":
            mine = [g for gid, g in self.groups.items() if user_id in self.members[gid]]
            return httpx.Response(200, json=mine)

        if path == "/api/groups/join":
            group = next(
                (g for g in self.groups.values() if g["inviteCode"] == body["inviteCode"]), None
            )
            if group is None:
                return httpx.Response(404, json={"message": "Группа не найдена"})
            if user_id in self.members[group["id"]]:
                return httpx.Response(400, json={"message": "Вы уже состоите в этой группе"})
            self.members[group["id"]].add(user_id)
            return httpx.Response(200, json={"message": "ok", "groupId": group["id"]})

        if path.startswith("/api/groups/") and path.endswith("/members"):
            group_id = path.split("/")[3]
            users_by_id = {u["id"]: u for u in self.users.values()}
            rows = [
                {
                    "userId": uid,
                    "role": "owner" if self.groups[group_id]["ownerId"] == uid else "member",
                    "User": {"id": uid, "name": users_by_id[uid]["name"]},
                }
                for uid in self.members[group_id]
            ]
            return httpx.Response(200, json=rows)

        if path == "/api/categories" and request.method == "GET":
            group_id = request.url.params.get("groupId")
            rows = [c for c in self.categories if c["groupId"] in (None, group_id)]
            return httpx.Response(200, json=rows)

        if path == "/api/categories" and request.method == "POST":
            category = {
                "id": f"c{next(self._ids)}",
                "name": body["name"],
                "icon": None,
                "groupId": body.get("groupId"),
            }
            self.categories.append(category)
            return httpx.Response(201, json=category)

        if path == "/api/savings-goals" and request.method == "POST":
            return httpx.Response(
                201,
                json=self.add_goal(
                    body["groupId"], body["name"], body.get("type", "group"), body["targetAmount"]
                ),
            )

        if path.startswith("/api/savings-goals/group/"):
            group_id = path.rsplit("/", 1)[1]
            return httpx.Response(200, json=[g for g in self.goals if g["groupId"] == group_id])

        if path.startswith("/api/savings-goals/") and path.endswith("/contribute"):
            goal_id = path.split("/")[3]
            goal = next((g for g in self.goals if g["id"] == goal_id), None)
            if goal is None:
                return httpx.Response(404, json={"message": "Копилка не найдена"})
            self.contributions.append({"goalId": goal_id, "userId": user_id, **body})
            goal["currentAmount"] = f"{float(goal['currentAmount']) + body['amount']:.2f}"
            return httpx.Response(200, json=goal)

        if path == "/api/achievements" and request.method == "GET":
            earned = self.unlocked.get(user_id, set())
            return httpx.Response(
                200,
                json=[
                    {
                        **row,
                        "earnedAt": "2026-09-06T12:00:00.000Z" if row["code"] in earned else None,
                    }
                    for row in _ACHIEVEMENTS
                ],
            )

        if path == "/api/achievements/check" and request.method == "POST":
            fresh = self._unlock(user_id)
            return httpx.Response(
                200, json=[row for row in _ACHIEVEMENTS if row["code"] in fresh]
            )

        if path == "/api/reminders/ack" and request.method == "POST":
            settings = self._reminder(user_id)
            settings["lastRemindedAt"] = "2026-09-06T12:00:00.000Z"
            return httpx.Response(200, json=settings)

        if path == "/api/reminders" and request.method == "GET":
            return httpx.Response(200, json=self._reminder(user_id))

        if path == "/api/reminders" and request.method == "PUT":
            settings = self._reminder(user_id)
            if "style" in body:
                settings["style"] = body["style"]
            if "enabled" in body:
                settings["enabled"] = body["enabled"]
            return httpx.Response(200, json=settings)

        if path == "/api/expenses/receipt" and request.method == "POST":
            if self.receipt_broken:
                return httpx.Response(500, json={"message": "Не удалось распознать чек"})
            return httpx.Response(
                200,
                json={
                    "amount": 1234.56,
                    "date": "2026-09-06T00:00:00.000Z",
                    "category": "Продукты",
                    "description": "Магазин",
                },
            )

        if path == "/api/expenses" and request.method == "POST":
            if user_id not in self.members.get(body["groupId"], set()):
                return httpx.Response(403, json={"message": "Вы не состоите в этой группе"})
            expense = {"id": f"e{next(self._ids)}", "createdById": user_id, **body}
            self.expenses.append(expense)
            self._recalculate_debts(body["groupId"])
            return httpx.Response(201, json=expense)

        if path == "/api/debts/my":
            rows = [
                self._debt_with_users(d)
                for d in self.debts
                if d["status"] == "pending" and user_id in (d["fromUserId"], d["toUserId"])
            ]
            return httpx.Response(200, json=rows)

        if path.startswith("/api/debts/group/"):
            group_id = path.rsplit("/", 1)[1]
            rows = [
                self._debt_with_users(d)
                for d in self.debts
                if d["groupId"] == group_id and d["status"] == "pending"
            ]
            return httpx.Response(200, json=rows)

        if path.startswith("/api/debts/") and path.endswith("/pay"):
            debt_id = path.split("/")[3]
            debt = next((d for d in self.debts if d["id"] == debt_id), None)
            if debt is None or debt["status"] != "pending":
                return httpx.Response(404, json={"message": "Долг не найден или уже погашен"})
            if body["amount"] > debt["amount"]:
                return httpx.Response(400, json={"message": "Сумма превышает остаток долга"})
            self.payments.append(
                {"debtId": debt_id, "amount": body["amount"], "fromUserId": debt["fromUserId"]}
            )
            debt["amount"] = round(debt["amount"] - body["amount"], 2)
            if debt["amount"] == 0:
                debt["status"] = "settled"
            return httpx.Response(200, json=debt)

        return httpx.Response(404, json={"message": f"no route {path}"})

    # --- долги: та же жадная схема, что и в бэкенде ---

    def _recalculate_debts(self, group_id: str) -> None:
        balances: dict[str, float] = {}
        for expense in self.expenses:
            if expense["groupId"] != group_id:
                continue
            balances[expense["payerId"]] = balances.get(expense["payerId"], 0) + expense["amount"]
            for split in expense["splits"]:
                balances[split["userId"]] = balances.get(split["userId"], 0) - split["amountOwed"]
        self.debts = [d for d in self.debts if d["groupId"] != group_id]
        creditors = [[uid, net] for uid, net in balances.items() if net > 0.01]
        debtors = [[uid, -net] for uid, net in balances.items() if net < -0.01]
        while debtors and creditors:
            amount = round(min(debtors[0][1], creditors[0][1]), 2)
            self.debts.append(
                {
                    "id": f"d{next(self._ids)}",
                    "groupId": group_id,
                    "fromUserId": debtors[0][0],
                    "toUserId": creditors[0][0],
                    "amount": amount,
                    "status": "pending",
                }
            )
            debtors[0][1] -= amount
            creditors[0][1] -= amount
            if debtors[0][1] < 0.01:
                debtors.pop(0)
            if creditors[0][1] < 0.01:
                creditors.pop(0)

    def _debt_with_users(self, debt: dict) -> dict:
        users_by_id = {u["id"]: u for u in self.users.values()}

        def brief(uid: str) -> dict:
            user = users_by_id[uid]
            return {"id": uid, "name": user["name"], "telegramId": user["telegramId"]}

        return {**debt, "fromUser": brief(debt["fromUserId"]), "toUser": brief(debt["toUserId"])}

    def _unlock(self, user_id: str) -> set[str]:
        earned = self.unlocked.setdefault(user_id, set())
        codes: set[str] = set()
        expenses = sum(1 for e in self.expenses if e.get("createdById") == user_id)
        if expenses >= 1:
            codes.add("first_expense")
        if expenses >= 3:
            codes.add("three_expenses")
        if any(p.get("fromUserId") == user_id for p in self.payments):
            codes.add("first_payment")
        if any(c.get("userId") == user_id for c in self.contributions):
            codes.add("first_contribute")
        if any(g.get("ownerId") == user_id for g in self.groups.values()):
            codes.add("first_group")
        fresh = codes - earned
        earned.update(fresh)
        return fresh

    def _reminder(self, user_id: str) -> dict:
        return self.reminders.setdefault(
            user_id, {"style": "neutral", "enabled": True, "lastRemindedAt": None}
        )

    def _authorize(self, request: httpx.Request) -> str | None:
        auth = request.headers.get("Authorization", "")
        token = auth.removeprefix("Bearer ").strip()
        if token not in self.valid_tokens:
            return None
        return token.split("-")[1]
