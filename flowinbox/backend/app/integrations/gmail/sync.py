import logging
import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.email import EmailThread, Email
from app.integrations.gmail.client import GmailClient
from datetime import datetime, timezone

logger = logging.getLogger("flowinbox.integrations.gmail_sync")

def _to_utc(dt):
    if not dt:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


import gc

class GmailSyncService:
    """Ingest synced emails from Gmail into PostgreSQL user-scoped tables."""

    @staticmethod
    async def sync_user_inbox(db: AsyncSession, user_id: uuid.UUID, access_token: str) -> int:
        client = GmailClient(access_token)
        
        # Streamlined query list with max_results=10 to keep RAM below 512MB limit on Render
        queries = ["in:inbox", "category:promotions", "is:sent"]
        all_messages = []
        seen_ids = set()

        for q in queries:
            try:
                msgs = await client.fetch_messages(max_results=10, query=q)
                for m in msgs:
                    if m["gmail_id"] not in seen_ids:
                        seen_ids.add(m["gmail_id"])
                        all_messages.append(m)
            except Exception as err:
                logger.warning(f"[GmailSync] Error fetching query '{q}': {str(err)}")

        synced_count = 0

        for msg in all_messages:
            label_ids = msg.get("label_ids", [])
            is_starred = "STARRED" in label_ids
            is_unread = "UNREAD" in label_ids
            is_trashed = "TRASH" in label_ids
            is_spam = "SPAM" in label_ids
            is_sent = "SENT" in label_ids
            is_draft = "DRAFT" in label_ids
            is_inbox = "INBOX" in label_ids

            folder = "all"
            if is_trashed:
                folder = "trash"
            elif is_spam:
                folder = "spam"
            elif is_draft:
                folder = "drafts"
            elif is_sent:
                folder = "sent"
            elif is_inbox:
                folder = "inbox"
            elif is_starred:
                folder = "starred"

            msg_sent_at = _to_utc(msg.get("sent_at")) or datetime.now(timezone.utc)

            # Check if thread exists
            stmt = select(EmailThread).where(
                EmailThread.user_id == user_id,
                EmailThread.gmail_thread_id == msg["gmail_thread_id"]
            )
            res = await db.execute(stmt)
            thread = res.scalars().first()

            if not thread:
                thread = EmailThread(
                    user_id=user_id,
                    gmail_thread_id=msg["gmail_thread_id"],
                    subject=msg["subject"],
                    snippet=msg.get("snippet") or msg["body_text"][:200],
                    last_message_at=msg_sent_at,
                    category=msg.get("category", "primary"),
                    importance=msg.get("importance", "normal"),
                    needs_reply=msg.get("needs_reply", False),
                    has_unanswered_followup=False,
                    folder=folder,
                    is_starred=is_starred,
                    is_read=not is_unread,
                    is_archived=not is_inbox and not is_trashed and not is_spam and not is_sent,
                    is_trashed=is_trashed
                )
                db.add(thread)
                await db.flush()
            else:
                # Idempotent update of thread properties
                thread.subject = msg["subject"]
                if msg.get("snippet"):
                    thread.snippet = msg["snippet"]
                thread_last = _to_utc(thread.last_message_at)
                if msg_sent_at and (not thread_last or msg_sent_at > thread_last):
                    thread.last_message_at = msg_sent_at

                if is_starred:
                    thread.is_starred = True
                thread.is_read = not is_unread
                thread.is_trashed = is_trashed
                if is_inbox:
                    thread.folder = "inbox"
                elif is_sent and thread.folder != "inbox":
                    thread.folder = "sent"
                elif is_draft and thread.folder != "inbox":
                    thread.folder = "drafts"

            # Check if email message exists
            email_stmt = select(Email).where(Email.gmail_id == msg["gmail_id"])
            email_res = await db.execute(email_stmt)
            existing_email = email_res.scalars().first()

            if not existing_email:
                email = Email(
                    user_id=user_id,
                    thread_id=thread.id,
                    gmail_id=msg["gmail_id"],
                    sender=msg["sender"],
                    sender_email=msg["sender_email"],
                    recipients=msg["recipients"],
                    subject=msg["subject"],
                    body_text=msg["body_text"],
                    sent_at=msg_sent_at,

                    is_incoming=msg["is_incoming"]
                )
                db.add(email)
                synced_count += 1

        await db.commit()
        return synced_count
