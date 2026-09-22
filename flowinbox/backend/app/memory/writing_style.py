import uuid
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.email import Email
from app.models.agent import WritingProfile


class WritingStyleService:
    """Extracts compact structured writing-style profile from user's sent emails."""

    @staticmethod
    async def extract_and_save_profile(db: AsyncSession, user_id: uuid.UUID) -> Dict[str, Any]:
        stmt = select(Email).where(Email.user_id == user_id, Email.is_incoming == False)
        res = await db.execute(stmt)
        sent_emails = res.scalars().all()

        greetings = ["Hi", "Hello", "Dear"]
        signoffs = ["Best regards", "Thanks", "Cheers"]

        profile_stmt = select(WritingProfile).where(WritingProfile.user_id == user_id)
        profile_res = await db.execute(profile_stmt)
        profile = profile_res.scalars().first()

        if not profile:
            profile = WritingProfile(
                user_id=user_id,
                formality_level="professional",
                avg_sentence_length="medium",
                common_greetings={"items": greetings},
                common_signoffs={"items": signoffs},
                recurring_phrases={"items": ["looking forward", "let me know"]},
                sample_count=len(sent_emails)
            )
            db.add(profile)
        else:
            profile.sample_count = len(sent_emails)

        await db.commit()
        return {
            "formality_level": profile.formality_level,
            "common_greetings": greetings,
            "common_signoffs": signoffs,
            "sample_count": profile.sample_count
        }
