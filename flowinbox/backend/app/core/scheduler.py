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

                from datetime import datetime, timezone, timedelta
                from app.integrations.oauth.google import GoogleOAuthService
                from app.core.security import encrypt_token

                for acc in oauth_accounts:
                    try:
                        plain_token = decrypt_token(acc.encrypted_access_token)
                        
                        # Auto-refresh token if expired or about to expire in 5 minutes
                        now = datetime.now(timezone.utc)
                        if acc.encrypted_refresh_token and (not acc.expires_at or acc.expires_at <= now or (acc.expires_at - now).total_seconds() < 300):
                            try:
                                ref_token = decrypt_token(acc.encrypted_refresh_token)
                                ref_res = await GoogleOAuthService.refresh_access_token(ref_token)
                                if ref_res and "access_token" in ref_res:
                                    plain_token = ref_res["access_token"]
                                    acc.encrypted_access_token = encrypt_token(plain_token)
                                    expires_in = ref_res.get("expires_in", 3600)
                                    acc.expires_at = now + timedelta(seconds=expires_in)
                                    await db.commit()
                                    logger.info(f"[GmailScheduler] Automatically refreshed OAuth access token for user {acc.user_id}")
                            except Exception as ref_err:
                                logger.warning(f"[GmailScheduler] Token refresh failed for user {acc.user_id}: {str(ref_err)}")

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
