import asyncio
import logging

from obshak_bot.services.auth import TelegramUser
from obshak_bot.services.notifications import Notifier
from obshak_bot.services.reminders import ReminderService
from obshak_bot.storage import UserSessionRepository

log = logging.getLogger(__name__)


async def reminder_loop(
    sessions: UserSessionRepository,
    reminders: ReminderService,
    notifier: Notifier,
    check_seconds: float,
) -> None:
    """Периодически напоминает о долгах тем, у кого напоминания включены."""
    while True:
        await asyncio.sleep(check_seconds)
        try:
            await tick(sessions, reminders, notifier)
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("Reminder tick failed")


async def tick(
    sessions: UserSessionRepository, reminders: ReminderService, notifier: Notifier
) -> int:
    sent = 0
    for session in await sessions.list_all():
        actor = TelegramUser(id=session.telegram_id, name="")
        try:
            text = await reminders.due_text(actor)
            if text is None:
                continue
            if await notifier.send(actor.id, text):
                await reminders.ack(actor)
                sent += 1
        except Exception:
            log.warning("Reminder skipped for %s", actor.id, exc_info=True)
    if sent:
        log.info("Sent %d debt reminders", sent)
    return sent
