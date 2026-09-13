import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from obshak_bot.api import ObshakApiClient
from obshak_bot.config import Settings
from obshak_bot.handlers import build_root_router
from obshak_bot.middlewares import AutoJoinMiddleware, DedupUpdateMiddleware
from obshak_bot.services import (
    AchievementService,
    AuthService,
    DebtService,
    ExpenseService,
    GroupService,
    Notifier,
    PiggyBankService,
    ReceiptService,
    ReminderService,
)
from obshak_bot.services.scheduler import reminder_loop
from obshak_bot.storage import (
    ChatGroupRepository,
    Database,
    ProcessedUpdateRepository,
    UserSessionRepository,
)

log = logging.getLogger("obshak_bot")

_PROCESSED_UPDATES_RETENTION_DAYS = 7


async def run() -> None:
    settings = Settings()
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)

    db = Database(settings.db_path)
    await db.connect()
    processed_updates = ProcessedUpdateRepository(db)
    sessions = UserSessionRepository(db)
    chats = ChatGroupRepository(db)

    api = ObshakApiClient(str(settings.backend_url), settings.backend_timeout_seconds)
    bot = Bot(
        settings.bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    auth = AuthService(api, sessions)
    groups = GroupService(api, auth, sessions, chats)

    dispatcher = Dispatcher()
    dispatcher.update.outer_middleware(DedupUpdateMiddleware(processed_updates))
    dispatcher.message.outer_middleware(AutoJoinMiddleware(groups))
    dispatcher["auth"] = auth
    dispatcher["groups"] = groups
    dispatcher["expenses"] = ExpenseService(api, auth)
    debts = DebtService(api, auth)
    dispatcher["debts"] = debts
    dispatcher["piggy"] = PiggyBankService(api, auth)
    dispatcher["receipts"] = ReceiptService(api, auth)
    reminders = ReminderService(api, auth, debts, settings.reminder_interval_hours)
    dispatcher["reminders"] = reminders
    dispatcher["achievements"] = AchievementService(api, auth)
    dispatcher["notifier"] = Notifier(bot, sessions, chats)
    dispatcher.include_router(build_root_router())

    reminder_task = asyncio.create_task(
        reminder_loop(sessions, reminders, dispatcher["notifier"], settings.reminder_check_seconds)
    )
    try:
        purged = await processed_updates.purge_older_than(_PROCESSED_UPDATES_RETENTION_DAYS)
        me = await bot.get_me()
        log.info(
            "Started as @%s, backend=%s, db=%s, purged %d old updates",
            me.username,
            settings.backend_url,
            settings.db_path,
            purged,
        )
        # Не отвечать пачкой на сообщения, накопившиеся пока бот был выключен.
        await bot.delete_webhook(drop_pending_updates=True)
        await dispatcher.start_polling(bot)
    finally:
        reminder_task.cancel()
        await api.aclose()
        await bot.session.close()
        await db.close()


if __name__ == "__main__":
    asyncio.run(run())
