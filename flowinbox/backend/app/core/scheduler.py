import asyncio
import logging
from sqlalchemy import select
from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.user import OAuthAccount
from app.core.security import decrypt_token
from app.integrations.gmail.sync import GmailSyncService

logger = logging.getLogger("flowinbox.core.scheduler")


_scheduler_task: asyncio.Task = None
_scheduler_running: bool = False


async def _gmail_sync_loop(interval_seconds: int = 90):
    """Background task loop that periodically syncs Gmail for all connected OAuth users."""
    global _scheduler_running
    logger.info(f"[GmailScheduler] Background Gmail sync loop started (Interval: {interval_seconds}s)")

    while _scheduler_running:
        try:
            async with AsyncSessionLocal() as db:
                stmt = select(OAuthAccount).where(OAuthAccount.provider == "google")
                res = await db.execute(stmt)
                oauth_accounts = res.scalars().all()

                for acc in oauth_accounts:
                    try:
                        plain_token = decrypt_token(acc.encrypted_access_token)
                        count = await GmailSyncService.sync_user_inbox(db, acc.user_id, plain_token)
                        if count > 0:
                            logger.info(f"[GmailScheduler] Auto-synced {count} new message(s) for user {acc.user_id}")
                    except Exception as user_err:
                        logger.warning(f"[GmailScheduler] Failed to sync user {acc.user_id}: {str(user_err)}")
        except Exception as loop_err:
            logger.error(f"[GmailScheduler] Error during scheduled sync iteration: {str(loop_err)}")

        # Wait for the next polling interval
        try:
            await asyncio.sleep(interval_seconds)
        except asyncio.CancelledError:
            logger.info("[GmailScheduler] Background sync loop cancelled.")
            break


def start_scheduler():
    """Start the background sync scheduler task during FastAPI lifespan startup."""
    global _scheduler_task, _scheduler_running
    if not settings.ENABLE_GMAIL_SYNC:
        logger.info("[GmailScheduler] Background sync disabled via settings (ENABLE_GMAIL_SYNC=false).")
        return

    if not _scheduler_running:
        _scheduler_running = True
        _scheduler_task = asyncio.create_task(_gmail_sync_loop(interval_seconds=90))
        logger.info("[GmailScheduler] Background scheduler initialized.")


def stop_scheduler():
    """Cancel the background sync scheduler task during FastAPI lifespan shutdown."""
    global _scheduler_task, _scheduler_running
    if _scheduler_running:
        _scheduler_running = False
        if _scheduler_task:
            _scheduler_task.cancel()
        logger.info("[GmailScheduler] Background scheduler stopped.")
