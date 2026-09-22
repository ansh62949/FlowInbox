import datetime
import base64
import email.utils
import email.mime.text
from typing import List, Dict, Any, Optional
import httpx


import re
import html

def _clean_html(raw_html: str) -> str:
    if not raw_html:
        return ""
    # Strip HTML tags and unescape entities
    text = re.sub(r'<[^>]+>', ' ', raw_html)
    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


class GmailClient:
    """Gmail API client wrapper querying official Google Gmail REST API v1."""

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {"Authorization": f"Bearer {access_token}"}

    async def fetch_messages(self, max_results: int = 50, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch real user messages from Google Gmail API v1."""
        if not self.access_token or self.access_token.startswith("mock_"):
            return []

        url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages?maxResults={max_results}"
        if query:
            url += f"&q={query}"

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=self.headers, timeout=12.0)
                if resp.status_code != 200:
                    print(f"[GmailClient] API list messages status {resp.status_code}: {resp.text}")
                    return []

                list_data = resp.json()
                message_stubs = list_data.get("messages", [])

                if not message_stubs:
                    return []

                parsed_messages = []
                for stub in message_stubs:
                    msg_id = stub.get("id")
                    if not msg_id:
                        continue

                    detail_url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}?format=full"
                    msg_resp = await client.get(detail_url, headers=self.headers, timeout=12.0)
                    if msg_resp.status_code != 200:
                        continue

                    msg_data = msg_resp.json()
                    parsed = self._parse_gmail_message(msg_data)
                    if parsed:
                        parsed_messages.append(parsed)

                return parsed_messages
        except Exception as err:
            print("[GmailClient] Network / API error during fetch_messages:", err)
            return []

    async def modify_message_labels(self, message_id: str, add_labels: List[str] = None, remove_labels: List[str] = None) -> bool:
        """Modify label IDs for a Gmail message via messages.modify."""
        if not self.access_token or self.access_token.startswith("mock_"):
            return False

        url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}/modify"
        payload = {
            "addLabelIds": add_labels or [],
            "removeLabelIds": remove_labels or []
        }
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, headers=self.headers, json=payload, timeout=10.0)
                return resp.status_code == 200
        except Exception as err:
            print(f"[GmailClient] Failed to modify labels for message {message_id}:", err)
            return False

    async def star_message(self, message_id: str, is_starred: bool = True) -> bool:
        """Add or remove STARRED label from Gmail message."""
        if is_starred:
            return await self.modify_message_labels(message_id, add_labels=["STARRED"])
        return await self.modify_message_labels(message_id, remove_labels=["STARRED"])

    async def mark_read(self, message_id: str, is_read: bool = True) -> bool:
        """Mark message as read or unread."""
        if is_read:
            return await self.modify_message_labels(message_id, remove_labels=["UNREAD"])
        return await self.modify_message_labels(message_id, add_labels=["UNREAD"])

    async def archive_message(self, message_id: str) -> bool:
        """Archive message by removing INBOX label."""
        return await self.modify_message_labels(message_id, remove_labels=["INBOX"])

    async def trash_message(self, message_id: str) -> bool:
        """Trash message via messages.trash."""
        if not self.access_token or self.access_token.startswith("mock_"):
            return False
        url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}/trash"
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, headers=self.headers, timeout=10.0)
                return resp.status_code == 200
        except Exception as err:
            print(f"[GmailClient] Trash message error {message_id}:", err)
            return False

    async def spam_message(self, message_id: str) -> bool:
        """Mark message as SPAM."""
        return await self.modify_message_labels(message_id, add_labels=["SPAM"], remove_labels=["INBOX"])

    async def send_email(self, to_email: str, subject: str, body: str, thread_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Send an actual email message using Google Gmail REST API v1."""
        if not self.access_token or self.access_token.startswith("mock_"):
            return None

        url = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
        msg = email.mime.text.MIMEText(body)
        msg['to'] = to_email
        msg['subject'] = subject
        raw_msg = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')
        
        payload = {"raw": raw_msg}
        if thread_id:
            payload["threadId"] = thread_id

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, headers=self.headers, json=payload, timeout=12.0)
                if resp.status_code == 200:
                    return resp.json()
                print(f"[GmailClient] send_email failed status {resp.status_code}: {resp.text}")
                return None
        except Exception as err:
            print("[GmailClient] Network error during send_email:", err)
            return None

    async def fetch_labels(self) -> List[Dict[str, Any]]:
        """Fetch list of user and system labels from Gmail API."""
        if not self.access_token or self.access_token.startswith("mock_"):
            return []
        url = "https://gmail.googleapis.com/gmail/v1/users/me/labels"
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=self.headers, timeout=10.0)
                if resp.status_code == 200:
                    return resp.json().get("labels", [])
                return []
        except Exception as err:
            print("[GmailClient] fetch_labels error:", err)
            return []

    def _parse_gmail_message(self, msg_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            gmail_id = msg_data.get("id")
            thread_id = msg_data.get("threadId")
            raw_snippet = msg_data.get("snippet", "")
            payload = msg_data.get("payload", {})
            headers = payload.get("headers", [])

            header_dict = {h.get("name", "").lower(): h.get("value", "") for h in headers}

            subject = header_dict.get("subject", "(No Subject)")
            sender = header_dict.get("from", "Unknown Sender")
            recipients = header_dict.get("to", "")
            date_str = header_dict.get("date")

            sent_at = datetime.datetime.now(datetime.timezone.utc)
            if date_str:
                try:
                    parsed_date = email.utils.parsedate_to_datetime(date_str)
                    if parsed_date:
                        if parsed_date.tzinfo is None:
                            parsed_date = parsed_date.replace(tzinfo=datetime.timezone.utc)
                        sent_at = parsed_date.astimezone(datetime.timezone.utc)
                except Exception:
                    pass


            # Extract body text safely
            raw_body = ""
            parts = payload.get("parts", [])
            if not parts and "body" in payload:
                body_data = payload["body"].get("data")
                if body_data:
                    try:
                        raw_body = base64.urlsafe_b64encode(body_data).decode("utf-8", errors="ignore")
                    except Exception:
                        pass
            else:
                for part in parts:
                    if part.get("mimeType") == "text/plain":
                        bdata = part.get("body", {}).get("data")
                        if bdata:
                            try:
                                raw_body = base64.urlsafe_b64encode(bdata).decode("utf-8", errors="ignore")
                                break
                            except Exception:
                                pass
                if not raw_body:
                    for part in parts:
                        if part.get("mimeType") == "text/html":
                            bdata = part.get("body", {}).get("data")
                            if bdata:
                                try:
                                    raw_body = base64.urlsafe_b64encode(bdata).decode("utf-8", errors="ignore")
                                    break
                                except Exception:
                                    pass

            # Clean raw HTML tags and entities
            clean_body = _clean_html(raw_body) if ("<" in raw_body and ">" in raw_body) else raw_body.strip()
            clean_snippet = html.unescape(raw_snippet).strip() if raw_snippet else clean_body[:200]

            # Determine category & reply need
            label_ids = msg_data.get("labelIds", [])
            is_incoming = "SENT" not in label_ids

            importance = "normal"
            if "IMPORTANT" in label_ids or "STARRED" in label_ids:
                importance = "high"

            category = "primary"
            if "CATEGORY_PROMOTIONS" in label_ids:
                category = "promotions"
            elif "CATEGORY_SOCIAL" in label_ids:
                category = "social"
            elif "CATEGORY_UPDATES" in label_ids:
                category = "updates"
            elif any(k in subject.lower() or k in sender.lower() for k in ["interview", "recruiter", "offer", "apply", "job", "career"]):
                category = "recruiter"
                importance = "urgent"

            needs_reply = is_incoming and any(
                q in clean_body.lower() or q in subject.lower() for q in ["?", "please let me know", "follow up", "confirm", "available", "schedule", "interview", "reply"]
            )

            sender_email = sender
            if "<" in sender and ">" in sender:
                sender_email = sender.split("<")[1].split(">")[0]

            return {
                "gmail_id": gmail_id,
                "gmail_thread_id": thread_id,
                "sender": sender,
                "sender_email": sender_email,
                "recipients": recipients,
                "subject": subject,
                "snippet": clean_snippet,
                "body_text": clean_body or clean_snippet,
                "sent_at": sent_at,
                "is_incoming": is_incoming,
                "category": category,
                "importance": importance,
                "needs_reply": needs_reply,
                "label_ids": label_ids
            }
        except Exception as err:
            print("[GmailClient] Error parsing message:", err)
            return None
