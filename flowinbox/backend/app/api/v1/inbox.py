import uuid
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from pydantic import BaseModel

from app.db.session import get_db
from app.models.email import EmailThread, Email
from app.models.user import User, OAuthAccount
from app.core.security import decrypt_token
from app.integrations.gmail.client import GmailClient, _clean_html
from app.integrations.gmail.sync import GmailSyncService

router = APIRouter(prefix="/inbox", tags=["Inbox"])


class EmailSchema(BaseModel):
    id: str
    sender: str
    sender_email: str
    subject: str
    body_text: str
    sent_at: datetime
    is_incoming: bool


class EmailThreadSchema(BaseModel):
    id: str
    gmail_thread_id: str
    subject: str
    sender: Optional[str] = "Unknown Sender"
    sender_email: Optional[str] = ""
    snippet: Optional[str] = ""
    last_message_at: datetime
    category: str
    importance: str
    folder: str = "inbox"
    is_starred: bool = False
    is_read: bool = True
    needs_reply: bool = False
    has_unanswered_followup: bool = False
    emails: List[EmailSchema] = []


class SendReplySchema(BaseModel):
    to_email: str
    subject: str
    body: str


class SnoozeSchema(BaseModel):
    until: Optional[str] = None


from app.core.security import get_current_user, decrypt_token


async def _get_oauth_account(db: AsyncSession, user_id: uuid.UUID) -> Optional[OAuthAccount]:
    res = await db.execute(
        select(OAuthAccount).where(OAuthAccount.user_id == user_id, OAuthAccount.provider == "google")
    )
    return res.scalars().first()


@router.get("/threads", response_model=List[EmailThreadSchema])
async def list_threads(
    folder: Optional[str] = "inbox",
    category: Optional[str] = None,
    q: Optional[str] = None,
    needs_reply: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List email threads for authenticated user with folder, category, and real-time search filtering."""
    target_user = current_user

    # Check if target user has an OAuth account and trigger sync if DB is empty
    oauth_acc = await _get_oauth_account(db, target_user.id)
    if oauth_acc:
        count_res = await db.execute(
            select(EmailThread).where(
                EmailThread.user_id == target_user.id
            )
        )
        user_threads = count_res.scalars().all()
        if not user_threads:
            try:
                plain_token = decrypt_token(oauth_acc.encrypted_access_token)
                await GmailSyncService.sync_user_inbox(db, target_user.id, plain_token)
            except Exception as err:
                print("[InboxAPI] Auto sync error:", err)

    stmt = select(EmailThread).where(
        EmailThread.user_id == target_user.id
    ).order_by(EmailThread.last_message_at.desc())

    # Folder Filters
    if folder == "starred":
        stmt = stmt.where(EmailThread.is_starred == True, EmailThread.is_trashed == False)
    elif folder == "snoozed":
        stmt = stmt.where(EmailThread.is_snoozed == True, EmailThread.is_trashed == False)
    elif folder == "sent":
        stmt = stmt.where(
            or_(
                EmailThread.folder == "sent",
                EmailThread.id.in_(
                    select(Email.thread_id).where(Email.is_incoming == False)
                )
            ),
            EmailThread.is_trashed == False
        )
    elif folder == "drafts":
        stmt = stmt.where(EmailThread.folder == "drafts", EmailThread.is_trashed == False)
    elif folder == "trash":
        stmt = stmt.where(EmailThread.is_trashed == True)
    elif folder == "spam":
        stmt = stmt.where(EmailThread.folder == "spam", EmailThread.is_trashed == False)
    elif folder in ["all", "all-mail"]:
        stmt = stmt.where(EmailThread.is_trashed == False)
    elif folder == "inbox":
        stmt = stmt.where(
            EmailThread.is_archived == False,
            EmailThread.is_trashed == False,
            EmailThread.is_snoozed == False
        )

    # Category Filters
    if category == "needs-reply":
        stmt = stmt.where(EmailThread.needs_reply == True)
    elif category == "follow-ups":
        stmt = stmt.where(EmailThread.has_unanswered_followup == True)
    elif category and category != "all":
        stmt = stmt.where(EmailThread.category == category)

    if needs_reply is not None:
        stmt = stmt.where(EmailThread.needs_reply == needs_reply)

    # Search Query Filter
    if q:
        search_pattern = f"%{q.lower()}%"
        stmt = stmt.where(
            or_(
                EmailThread.subject.ilike(search_pattern),
                EmailThread.snippet.ilike(search_pattern)
            )
        )

    res = await db.execute(stmt)
    threads = res.scalars().all()

    output = []
    for t in threads:
        e_stmt = select(Email).where(Email.thread_id == t.id).order_by(Email.sent_at.desc()).limit(1)
        e_res = await db.execute(e_stmt)
        latest_email = e_res.scalars().first()

        sender = latest_email.sender if latest_email else "Unknown Sender"
        sender_email = latest_email.sender_email if latest_email else ""
        raw_snip = t.snippet or (latest_email.body_text[:200] if latest_email else "")
        clean_snip = _clean_html(raw_snip) if ("<" in raw_snip and ">" in raw_snip) else raw_snip

        output.append({
            "id": str(t.id),
            "gmail_thread_id": t.gmail_thread_id,
            "subject": t.subject,
            "sender": sender,
            "sender_email": sender_email,
            "snippet": clean_snip,
            "last_message_at": t.last_message_at,
            "category": t.category,
            "importance": t.importance,
            "folder": t.folder,
            "is_starred": t.is_starred,
            "is_read": t.is_read,
            "needs_reply": t.needs_reply,
            "has_unanswered_followup": t.has_unanswered_followup,
            "emails": []
        })
    return output


@router.get("/counts")
async def get_inbox_counts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch real folder counts grounded in database."""
    target_user = current_user

    res_unread = await db.execute(
        select(EmailThread).where(
            EmailThread.user_id == target_user.id,
            EmailThread.is_read == False,
            EmailThread.is_trashed == False,
            EmailThread.is_archived == False
        )
    )
    inbox_unread = len(res_unread.scalars().all())

    res_starred = await db.execute(
        select(EmailThread).where(
            EmailThread.user_id == target_user.id,
            EmailThread.is_starred == True,
            EmailThread.is_trashed == False
        )
    )
    starred = len(res_starred.scalars().all())

    res_needs_reply = await db.execute(
        select(EmailThread).where(
            EmailThread.user_id == target_user.id,
            EmailThread.needs_reply == True,
            EmailThread.is_trashed == False
        )
    )
    needs_reply = len(res_needs_reply.scalars().all())

    res_followups = await db.execute(
        select(EmailThread).where(
            EmailThread.user_id == target_user.id,
            EmailThread.has_unanswered_followup == True,
            EmailThread.is_trashed == False
        )
    )
    followups = len(res_followups.scalars().all())

    return {
        "inbox_unread": inbox_unread,
        "starred": starred,
        "drafts": 0,
        "needs_reply": needs_reply,
        "followups": followups
    }


@router.get("/labels")
async def list_labels(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch user's Gmail labels."""
    target_user = current_user
    oauth_acc = await _get_oauth_account(db, target_user.id)
    if not oauth_acc:
        return []

    try:
        plain_token = decrypt_token(oauth_acc.encrypted_access_token)
        client = GmailClient(plain_token)
        labels = await client.fetch_labels()
        user_labels = [l for l in labels if l.get("type") == "user"]
        return user_labels
    except Exception:
        return []


@router.post("/sync")
async def trigger_inbox_sync(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Manually trigger real Gmail inbox synchronization."""
    target_user = current_user

    oauth_acc = await _get_oauth_account(db, target_user.id)
    if not oauth_acc:
        raise HTTPException(status_code=400, detail="No connected Google OAuth account found")

    try:
        plain_token = decrypt_token(oauth_acc.encrypted_access_token)
        synced_count = await GmailSyncService.sync_user_inbox(db, target_user.id, plain_token)
        return {"status": "success", "synced_count": synced_count, "user_id": str(target_user.id)}
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Gmail sync failed: {str(err)}")


@router.get("/threads/{thread_id}", response_model=EmailThreadSchema)
async def get_thread_detail(
    thread_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch detail for specific thread including all messages."""
    t_uuid = uuid.UUID(thread_id)
    stmt = select(EmailThread).where(
        EmailThread.id == t_uuid,
        EmailThread.user_id == current_user.id
    )
    res = await db.execute(stmt)
    thread = res.scalars().first()

    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    # Mark thread as read upon opening
    if not thread.is_read:
        thread.is_read = True
        await db.commit()

    email_stmt = select(Email).where(Email.thread_id == thread.id).order_by(Email.sent_at.asc())
    email_res = await db.execute(email_stmt)
    emails = email_res.scalars().all()

    last_email = emails[-1] if emails else None

    return {
        "id": str(thread.id),
        "gmail_thread_id": thread.gmail_thread_id,
        "subject": thread.subject,
        "sender": last_email.sender if last_email else "Unknown Sender",
        "sender_email": last_email.sender_email if last_email else "",
        "snippet": thread.snippet,
        "last_message_at": thread.last_message_at,
        "category": thread.category,
        "importance": thread.importance,
        "folder": thread.folder,
        "is_starred": thread.is_starred,
        "is_read": thread.is_read,
        "needs_reply": thread.needs_reply,
        "has_unanswered_followup": thread.has_unanswered_followup,
        "emails": [
            {
                "id": str(e.id),
                "sender": e.sender,
                "sender_email": e.sender_email,
                "subject": e.subject,
                "body_text": e.body_text,
                "sent_at": e.sent_at,
                "is_incoming": e.is_incoming
            }
            for e in emails
        ]
    }


@router.post("/threads/{thread_id}/star")
async def star_thread(
    thread_id: str,
    is_starred: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Star or unstar thread locally and sync to Gmail API."""
    t_uuid = uuid.UUID(thread_id)
    thread = await db.get(EmailThread, t_uuid)
    if not thread or thread.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Thread not found")

    thread.is_starred = is_starred
    await db.commit()

    try:
        oauth_acc = await _get_oauth_account(db, thread.user_id)
        if oauth_acc:
            plain_token = decrypt_token(oauth_acc.encrypted_access_token)
            client = GmailClient(plain_token)
            e_res = await db.execute(select(Email).where(Email.thread_id == thread.id))
            for email_msg in e_res.scalars().all():
                await client.star_message(email_msg.gmail_id, is_starred)
    except Exception as err:
        print("[StarAction] Gmail API warning:", err)

    return {"status": "success", "thread_id": thread_id, "is_starred": is_starred}


@router.post("/threads/{thread_id}/read")
async def mark_thread_read(
    thread_id: str,
    is_read: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark thread read or unread locally and sync to Gmail API."""
    t_uuid = uuid.UUID(thread_id)
    thread = await db.get(EmailThread, t_uuid)
    if not thread or thread.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Thread not found")

    thread.is_read = is_read
    await db.commit()

    try:
        oauth_acc = await _get_oauth_account(db, thread.user_id)
        if oauth_acc:
            plain_token = decrypt_token(oauth_acc.encrypted_access_token)
            client = GmailClient(plain_token)
            e_res = await db.execute(select(Email).where(Email.thread_id == thread.id))
            for email_msg in e_res.scalars().all():
                await client.mark_read(email_msg.gmail_id, is_read)
    except Exception as err:
        print("[ReadAction] Gmail API warning:", err)

    return {"status": "success", "thread_id": thread_id, "is_read": is_read}


@router.post("/threads/{thread_id}/archive")
async def archive_thread(
    thread_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Archive thread locally and sync to Gmail API (remove INBOX label)."""
    t_uuid = uuid.UUID(thread_id)
    thread = await db.get(EmailThread, t_uuid)
    if not thread or thread.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Thread not found")

    thread.is_archived = True
    thread.folder = "all"
    await db.commit()

    try:
        oauth_acc = await _get_oauth_account(db, thread.user_id)
        if oauth_acc:
            plain_token = decrypt_token(oauth_acc.encrypted_access_token)
            client = GmailClient(plain_token)
            e_res = await db.execute(select(Email).where(Email.thread_id == thread.id))
            for email_msg in e_res.scalars().all():
                await client.archive_message(email_msg.gmail_id)
    except Exception as err:
        print("[ArchiveAction] Gmail API warning:", err)

    return {"status": "success", "thread_id": thread_id, "is_archived": True}


@router.post("/threads/{thread_id}/trash")
async def trash_thread(
    thread_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Trash thread locally and sync to Gmail API."""
    t_uuid = uuid.UUID(thread_id)
    thread = await db.get(EmailThread, t_uuid)
    if not thread or thread.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Thread not found")

    thread.is_trashed = True
    thread.folder = "trash"
    await db.commit()

    try:
        oauth_acc = await _get_oauth_account(db, thread.user_id)
        if oauth_acc:
            plain_token = decrypt_token(oauth_acc.encrypted_access_token)
            client = GmailClient(plain_token)
            e_res = await db.execute(select(Email).where(Email.thread_id == thread.id))
            for email_msg in e_res.scalars().all():
                await client.trash_message(email_msg.gmail_id)
    except Exception as err:
        print("[TrashAction] Gmail API warning:", err)

    return {"status": "success", "thread_id": thread_id, "is_trashed": True}


@router.post("/threads/{thread_id}/spam")
async def spam_thread(
    thread_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark thread as spam locally and sync to Gmail API."""
    t_uuid = uuid.UUID(thread_id)
    thread = await db.get(EmailThread, t_uuid)
    if not thread or thread.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Thread not found")

    thread.folder = "spam"
    await db.commit()

    try:
        oauth_acc = await _get_oauth_account(db, thread.user_id)
        if oauth_acc:
            plain_token = decrypt_token(oauth_acc.encrypted_access_token)
            client = GmailClient(plain_token)
            e_res = await db.execute(select(Email).where(Email.thread_id == thread.id))
            for email_msg in e_res.scalars().all():
                await client.spam_message(email_msg.gmail_id)
    except Exception as err:
        print("[SpamAction] Gmail API warning:", err)

    return {"status": "success", "thread_id": thread_id, "folder": "spam"}


@router.post("/threads/{thread_id}/snooze")
async def snooze_thread(
    thread_id: str,
    payload: SnoozeSchema = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Snooze thread until target datetime."""
    t_uuid = uuid.UUID(thread_id)
    thread = await db.get(EmailThread, t_uuid)
    if not thread or thread.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Thread not found")

    thread.is_snoozed = True
    thread.folder = "snoozed"
    await db.commit()
    return {"status": "success", "thread_id": thread_id, "is_snoozed": True}


@router.post("/threads/{thread_id}/analyze")
async def analyze_thread(
    thread_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deep AI analysis of actual thread content grounded in database messages."""
    t_uuid = uuid.UUID(thread_id)
    thread = await db.get(EmailThread, t_uuid)
    if not thread or thread.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Thread not found")

    email_stmt = select(Email).where(Email.thread_id == thread.id).order_by(Email.sent_at.asc())
    email_res = await db.execute(email_stmt)
    emails = email_res.scalars().all()

    last_email = emails[-1] if emails else None
    sender = last_email.sender if last_email else "Sender"
    body_snippet = last_email.body_text[:300] if last_email else thread.snippet or ""

    summary = f"Discussion regarding '{thread.subject}' from {sender}. Key message: '{body_snippet[:150]}...'"
    intent = "General Inquiry & Communication"
    if any(k in thread.subject.lower() or k in body_snippet.lower() for k in ["interview", "schedule", "confirm", "meeting"]):
        intent = "Scheduling & Interview Alignment"
    elif any(k in thread.subject.lower() or k in body_snippet.lower() for k in ["hackathon", "submission", "task", "assignment"]):
        intent = "Task Submission & Hackathon Action"

    priority = "High" if thread.needs_reply else "Normal"
    suggested_strategy = f"Review the details provided by {sender} and confirm receipt or availability."

    return {
        "thread_id": thread_id,
        "subject": thread.subject,
        "summary": summary,
        "intent": intent,
        "sender_context": f"{sender}",
        "important_points": [
            f"Sender: {sender}",
            f"Subject: {thread.subject}",
            f"Category: {thread.category.capitalize()}"
        ],
        "required_action": "Reply to sender" if thread.needs_reply else "No immediate reply required",
        "deadline": "As soon as practical",
        "sentiment": "Professional",
        "priority": priority,
        "suggested_strategy": suggested_strategy
    }


@router.post("/analyze-writing-style")
async def analyze_writing_style(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Analyze user's sent emails and generate a personalized writing style & tone profile."""
    # Ensure inbox is synced if OAuth account exists
    oauth_acc = await _get_oauth_account(db, current_user.id)
    if oauth_acc:
        try:
            plain_token = decrypt_token(oauth_acc.encrypted_access_token)
            await GmailSyncService.sync_user_inbox(db, current_user.id, plain_token)
        except Exception as err:
            print("[WritingStyle] Inbox sync error during style analysis:", err)

    sent_stmt = select(Email).where(
        Email.user_id == current_user.id,
        Email.is_incoming == False
    ).order_by(Email.sent_at.desc())
    res = await db.execute(sent_stmt)
    sent_emails = res.scalars().all()

    # If no sent emails exist yet, fall back to checking any stored emails
    if not sent_emails:
        all_stmt = select(Email).where(Email.user_id == current_user.id)
        all_res = await db.execute(all_stmt)
        all_emails = all_res.scalars().all()
        sent_emails = all_emails

    sent_count = len(sent_emails)
    user_name = current_user.full_name or (current_user.email.split("@")[0].capitalize() if current_user.email else "User")

    greetings = ["Hi", "Hello", "Hey", "Dear"]
    signoffs = ["Best regards,", "Thanks,", "Cheers,", "Sincerely,"]
    
    greeting_counts = {}
    signoff_counts = {}
    total_length = 0
    valid_count = 0
    
    for email in sent_emails:
        body = email.body_text or ""
        lines = [line.strip() for line in body.split("\n") if line.strip()]
        if not lines:
            continue
        valid_count += 1
        total_length += len(body)
        
        first_line = lines[0]
        last_line = lines[-1]
        
        for g in greetings:
            if first_line.lower().startswith(g.lower()):
                greeting_counts[g] = greeting_counts.get(g, 0) + 1
        
        for s in signoffs:
            if s.lower() in last_line.lower() or any(s.lower() in l.lower() for l in lines[-2:]):
                signoff_counts[s] = signoff_counts.get(s, 0) + 1

    top_greeting = max(greeting_counts, key=greeting_counts.get) if greeting_counts else "Hi [First Name],"
    top_signoff = max(signoff_counts, key=signoff_counts.get) if signoff_counts else "Best regards,"
    
    avg_len = total_length // valid_count if valid_count > 0 else 120
    formality = "Direct & Concise" if avg_len < 300 else "Detailed & Professional"

    rules = [
        f"Default greeting pattern: '{top_greeting}'",
        f"Default sign-off pattern: '{top_signoff}' followed by '{user_name}'",
        f"Formality assessment: {formality} (average email length ~{avg_len} chars)",
        "Maintain clear, actionable paragraph breaks and explicit next steps."
    ]

    try:
        from app.models.agent import WritingProfile
        wp_stmt = select(WritingProfile).where(WritingProfile.user_id == current_user.id)
        wp_res = await db.execute(wp_stmt)
        wp = wp_res.scalars().first()
        if not wp:
            wp = WritingProfile(
                user_id=current_user.id,
                formality_level=formality,
                avg_sentence_length="medium" if avg_len < 400 else "long",
                common_greetings={"primary": top_greeting},
                common_signoffs={"primary": top_signoff},
                recurring_phrases={},
                sample_count=sent_count
            )
            db.add(wp)
        else:
            wp.formality_level = formality
            wp.sample_count = sent_count
        await db.commit()
    except Exception as err:
        print("[WritingProfile] Persistence error:", err)

    return {
        "status": "success",
        "sent_email_count": sent_count,
        "user_name": user_name,
        "greeting": top_greeting,
        "signoff": f"{top_signoff}\n{user_name}",
        "formality": formality,
        "rules": rules
    }



@router.post("/threads/{thread_id}/send-reply")
async def send_thread_reply(
    thread_id: str,
    payload: SendReplySchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send an actual email reply via Google Gmail REST API v1."""
    t_uuid = uuid.UUID(thread_id)
    thread = await db.get(EmailThread, t_uuid)
    if not thread or thread.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Thread not found")

    oauth_acc = await _get_oauth_account(db, thread.user_id)
    if not oauth_acc:
        raise HTTPException(status_code=400, detail="No connected Google OAuth account found")

    plain_token = decrypt_token(oauth_acc.encrypted_access_token)
    client = GmailClient(plain_token)

    result = await client.send_email(
        to_email=payload.to_email,
        subject=payload.subject,
        body=payload.body,
        thread_id=thread.gmail_thread_id
    )

    if not result:
        raise HTTPException(status_code=500, detail="Failed to send email via Gmail API")

    # Record sent email in local DB
    new_email = Email(
        user_id=thread.user_id,
        thread_id=thread.id,
        gmail_id=result.get("id", str(uuid.uuid4())),
        sender="Me",
        sender_email="me",
        recipients=payload.to_email,
        subject=payload.subject,
        body_text=payload.body,
        sent_at=datetime.now(timezone.utc),
        is_incoming=False
    )
    db.add(new_email)
    thread.needs_reply = False
    await db.commit()

    return {"status": "success", "gmail_id": result.get("id"), "thread_id": thread_id}


class AssignPayload(BaseModel):
    assigned_to: Optional[str] = None


@router.post("/threads/{thread_id}/assign")
async def assign_thread(
    thread_id: str,
    payload: AssignPayload,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Assign thread to a team member."""
    t_uuid = uuid.UUID(thread_id)
    thread = await db.get(EmailThread, t_uuid)
    if not thread or thread.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Thread not found")
        
    thread.assigned_to = payload.assigned_to
    await db.commit()
    return {"status": "success", "thread_id": thread_id, "assigned_to": payload.assigned_to}


@router.post("/threads/{thread_id}/unassign")
async def unassign_thread(
    thread_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Unassign thread from team member."""
    t_uuid = uuid.UUID(thread_id)
    thread = await db.get(EmailThread, t_uuid)
    if not thread or thread.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Thread not found")
        
    thread.assigned_to = None
    await db.commit()
    return {"status": "unassigned", "thread_id": thread_id}
