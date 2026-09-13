from aiogram import Router

from obshak_bot.handlers import (
    achievements_private,
    debts,
    errors,
    expenses,
    group_chat,
    groups_private,
    payer_confirmation,
    piggy,
    reminders,
    start,
)


def build_root_router() -> Router:
    root = Router(name="root")
    root.include_routers(
        errors.router,
        group_chat.router,
        start.router,
        groups_private.router,
        expenses.router,
        payer_confirmation.router,
        debts.router,
        piggy.router,
        reminders.router,
        achievements_private.router,
    )
    return root
