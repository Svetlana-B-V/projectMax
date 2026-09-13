from aiogram.filters.callback_data import CallbackData
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from obshak_bot.api import CategoryDto, DebtDto, GroupDto, SavingsGoalDto
from obshak_bot.money import format_amount

BTN_GROUPS = "👥 Группы"
BTN_EXPENSE = "💸 Расход"
BTN_RECEIPT = "📷 Чек"
BTN_DEBTS = "💰 Долги"
BTN_PIGGY = "🐷 Копилки"
BTN_REMINDERS = "🔔 Напоминания"
BTN_ACHIEVEMENTS = "🏆 Достижения"


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_EXPENSE), KeyboardButton(text=BTN_RECEIPT)],
            [KeyboardButton(text=BTN_DEBTS), KeyboardButton(text=BTN_PIGGY)],
            [KeyboardButton(text=BTN_REMINDERS), KeyboardButton(text=BTN_ACHIEVEMENTS)],
            [KeyboardButton(text=BTN_GROUPS)],
        ],
        resize_keyboard=True,
    )


class GroupCb(CallbackData, prefix="grp"):
    action: str  # select | members | invite | create | join | back
    group_id: str = ""


def groups_menu(groups: list[GroupDto], current_group_id: str | None) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=("✅ " if group.id == current_group_id else "") + group.name,
                callback_data=GroupCb(action="select", group_id=group.id).pack(),
            )
        ]
        for group in groups
    ]
    rows.append(
        [
            InlineKeyboardButton(text="➕ Создать", callback_data=GroupCb(action="create").pack()),
            InlineKeyboardButton(
                text="🔑 Вступить по коду", callback_data=GroupCb(action="join").pack()
            ),
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def group_card(group: GroupDto) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👤 Участники",
                    callback_data=GroupCb(action="members", group_id=group.id).pack(),
                ),
                InlineKeyboardButton(
                    text="🔗 Пригласить",
                    callback_data=GroupCb(action="invite", group_id=group.id).pack(),
                ),
            ],
            [InlineKeyboardButton(text="⬅️ К списку", callback_data=GroupCb(action="back").pack())],
        ]
    )


# --- добавление расхода ---


class ExpenseCb(CallbackData, prefix="exp"):
    action: str  # category | new_category | payer | toggle | all | done | split | save | cancel
    value: str = ""


def category_picker(categories: list[CategoryDto]) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"{c.icon} {c.name}" if c.icon else c.name,
                callback_data=ExpenseCb(action="category", value=c.id).pack(),
            )
        ]
        for c in categories
    ]
    rows.append(
        [
            InlineKeyboardButton(
                text="Без категории", callback_data=ExpenseCb(action="category").pack()
            ),
            InlineKeyboardButton(
                text="➕ Новая", callback_data=ExpenseCb(action="new_category").pack()
            ),
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def payer_picker(names: dict[str, str], me_user_id: str) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=("👤 Я — " if uid == me_user_id else "") + name,
                callback_data=ExpenseCb(action="payer", value=uid).pack(),
            )
        ]
        for uid, name in _me_first(names, me_user_id)
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def participants_picker(names: dict[str, str], selected: set[str]) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=("✅ " if uid in selected else "⬜ ") + name,
                callback_data=ExpenseCb(action="toggle", value=uid).pack(),
            )
        ]
        for uid, name in names.items()
    ]
    rows.append(
        [
            InlineKeyboardButton(text="Все", callback_data=ExpenseCb(action="all").pack()),
            InlineKeyboardButton(text="Готово ➡️", callback_data=ExpenseCb(action="done").pack()),
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def split_type_picker() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Поровну", callback_data=ExpenseCb(action="split", value="equal").pack()
                ),
                InlineKeyboardButton(
                    text="Вручную", callback_data=ExpenseCb(action="split", value="custom").pack()
                ),
            ]
        ]
    )


def confirm_expense() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Сохранить", callback_data=ExpenseCb(action="save").pack()
                ),
                InlineKeyboardButton(
                    text="❌ Отмена", callback_data=ExpenseCb(action="cancel").pack()
                ),
            ]
        ]
    )


class PayerConfirmCb(CallbackData, prefix="pconf"):
    """Ответ на «ты платил?». initiator — Telegram ID того, кто добавляет расход."""

    decision: str  # yes | no
    initiator: int
    token: str  # одноразовый код запроса, чтобы старые кнопки не срабатывали


def payer_confirmation(initiator: int, token: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Да, платил я",
                    callback_data=PayerConfirmCb(
                        decision="yes", initiator=initiator, token=token
                    ).pack(),
                ),
                InlineKeyboardButton(
                    text="❌ Нет",
                    callback_data=PayerConfirmCb(
                        decision="no", initiator=initiator, token=token
                    ).pack(),
                ),
            ]
        ]
    )


def _me_first(names: dict[str, str], me_user_id: str) -> list[tuple[str, str]]:
    return sorted(names.items(), key=lambda item: item[0] != me_user_id)


# --- долги ---


class DebtCb(CallbackData, prefix="debt"):
    action: str  # pay | pay_all | refresh
    value: str = ""


def debts_menu(i_owe: list[DebtDto]) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"↩️ Вернуть {_creditor_name(d)} · {format_amount(d.amount)}",
                callback_data=DebtCb(action="pay", value=d.id).pack(),
            )
        ]
        for d in i_owe
    ]
    rows.append(
        [InlineKeyboardButton(text="🔄 Обновить", callback_data=DebtCb(action="refresh").pack())]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _creditor_name(debt: DebtDto) -> str:
    return debt.to_user.name if debt.to_user else "?"


# --- копилки ---


class PiggyCb(CallbackData, prefix="pig"):
    action: str  # create | contrib | refresh
    value: str = ""


def piggy_menu(goals: list[SavingsGoalDto]) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"➕ Внести в «{g.name}»",
                callback_data=PiggyCb(action="contrib", value=g.id).pack(),
            )
        ]
        for g in goals
        if g.status == "active"
    ]
    rows.append(
        [
            InlineKeyboardButton(text="➕ Создать", callback_data=PiggyCb(action="create").pack()),
            InlineKeyboardButton(
                text="🔄 Обновить", callback_data=PiggyCb(action="refresh").pack()
            ),
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


class ReminderCb(CallbackData, prefix="rem"):
    action: str  # style | toggle
    value: str = ""


def reminders_menu(enabled: bool, style: str) -> InlineKeyboardMarkup:
    labels = {"soft": "Мягкий", "neutral": "Нейтральный", "playful": "Шутливый"}
    styles = [
        InlineKeyboardButton(
            text=("• " if key == style else "") + label,
            callback_data=ReminderCb(action="style", value=key).pack(),
        )
        for key, label in labels.items()
    ]
    toggle = "Выключить" if enabled else "Включить"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            styles,
            [InlineKeyboardButton(text=toggle, callback_data=ReminderCb(action="toggle").pack())],
        ]
    )


def pay_all_button() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Вернул всё", callback_data=DebtCb(action="pay_all").pack())]
        ]
    )
