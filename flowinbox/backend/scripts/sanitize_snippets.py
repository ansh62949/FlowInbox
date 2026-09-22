import asyncio
import re
import html
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.email import EmailThread

def _clean_html(raw_html: str) -> str:
    if not raw_html:
        return ""
    text = re.sub(r'<[^>]+>', ' ', raw_html)
    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

async def sanitize():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(EmailThread))
        threads = res.scalars().all()
        updated = 0
        for t in threads:
            if t.snippet and ("<" in t.snippet and ">" in t.snippet):
                t.snippet = _clean_html(t.snippet)[:200]
                updated += 1
        await db.commit()
        print(f"[Sanitize] Cleaned {updated} thread snippets in database.")

if __name__ == "__main__":
    asyncio.run(sanitize())
