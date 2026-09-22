import asyncio
import uuid
import datetime
from typing import List, Dict, Any

from app.retrieval.hybrid import HybridRetrievalPipeline
from app.vectorstore.factory import get_vector_store
from app.db.session import AsyncSessionLocal
from app.models.email import EmailThread, Email, Base
from app.models.user import User


async def run_hybrid_retrieval_eval():
    print("==================================================")
    print("  FlowInbox AI — Hybrid Retrieval Eval (§4 Spec) ")
    print("==================================================")

    test_user_a = uuid.uuid4()
    test_user_b = uuid.uuid4()

    emails_user_a = [
        {
            "id": str(uuid.uuid4()),
            "subject": "Google Backend Internship Interview Confirmation",
            "body_text": "We would love to schedule an interview with you tomorrow at 2 PM PST for the Backend role.",
        },
        {
            "id": str(uuid.uuid4()),
            "subject": "Follow up regarding Senior AI Engineer Position",
            "body_text": "Following up on your application for the AI Engineer position at TechCorp.",
        },
        {
            "id": str(uuid.uuid4()),
            "subject": "Weekly Tech Digest & Open Source AI Models",
            "body_text": "This week in tech: open source AI models are exploding across industry sectors.",
        }
    ]

    # Seed active vector store with user_a documents
    vstore = get_vector_store()
    await vstore.add_documents(
        ids=[em["id"] for em in emails_user_a],
        texts=[f"{em['subject']}\n{em['body_text']}" for em in emails_user_a],
        metadatas=[{"user_id": str(test_user_a), "subject": em["subject"]} for em in emails_user_a]
    )

    # Seed DB tables for lexical search leg
    async with AsyncSessionLocal() as db:
        try:
            # Create user_a in DB if not present
            user_obj = User(id=test_user_a, email=f"user_a_{test_user_a.hex[:6]}@example.com", hashed_password="pw")
            db.add(user_obj)
            await db.flush()

            thread_obj = EmailThread(
                user_id=test_user_a,
                gmail_thread_id=f"thread_{test_user_a.hex[:6]}",
                subject="Google Backend Internship",
                last_message_at=datetime.datetime.now(datetime.timezone.utc)
            )
            db.add(thread_obj)
            await db.flush()

            for em in emails_user_a:
                e_record = Email(
                    id=uuid.UUID(em["id"]),
                    user_id=test_user_a,
                    thread_id=thread_obj.id,
                    gmail_id=f"gmail_{em['id'][:8]}",
                    sender="Rahul Sharma (Google Recruiter)",
                    sender_email="rahul.recruiter@google.com",
                    recipients="test_user@example.com",
                    subject=em["subject"],
                    body_text=em["body_text"],
                    sent_at=datetime.datetime.now(datetime.timezone.utc)
                )
                db.add(e_record)
            await db.commit()
        except Exception:
            await db.rollback()

    async with AsyncSessionLocal() as db:
        pipeline = HybridRetrievalPipeline(db=db)

        # Query 1: Keyword/Exact Search
        res_1 = await pipeline.retrieve("Google Backend Internship", user_id=test_user_a, top_k=3)
        q1_pass = len(res_1) > 0 and "Google" in str(res_1[0])
        print(f"[Query 1 - Keyword Match] Hit count: {len(res_1)} | Top item ID: {res_1[0]['id'] if res_1 else None} | Pass: {q1_pass}")

        # Query 2: Semantic Match
        res_2 = await pipeline.retrieve("software developer interview timing", user_id=test_user_a, top_k=3)
        q2_pass = len(res_2) > 0
        print(f"[Query 2 - Semantic Match] Hit count: {len(res_2)} | Top item ID: {res_2[0]['id'] if res_2 else None} | Pass: {q2_pass}")

        # Query 3: Noise/Newsletter check
        res_3 = await pipeline.retrieve("TechCrunch open source newsletter", user_id=test_user_a, top_k=1)
        q3_pass = len(res_3) > 0 and ("Tech" in str(res_3[0]))
        print(f"[Query 3 - Noise/Newsletter] Hit count: {len(res_3)} | Top item ID: {res_3[0]['id'] if res_3 else None} | Pass: {q3_pass}")

        # Query 4: Out-of-domain query (assert low score/rejection)
        res_4 = await pipeline.retrieve("quantum physics particle accelerator", user_id=test_user_a, top_k=3)
        top_score = res_4[0]["score"] if res_4 else 0.0
        q4_pass = (top_score < 0.05 or len(res_4) == 0)
        print(f"[Query 4 - Out of Domain] Hit count: {len(res_4)} | Top score: {top_score:.4f} | Pass: {q4_pass}")

        # Query 5: User Isolation Check (CRITICAL SECURITY PROPERTY)
        res_isolation = await pipeline.retrieve("Google Backend Internship", user_id=test_user_b, top_k=5)
        user_isolation_pass = (len(res_isolation) == 0)
        print(f"[Query 5 - User Isolation] Querying user_b data when only user_a exists -> Hit count: {len(res_isolation)} | Pass: {user_isolation_pass}")

    print("--------------------------------------------------")
    print(f"Hybrid Retrieval Evaluation Summary:")
    print(f"   Keyword Search: {'PASS' if q1_pass else 'FAIL'}")
    print(f"   Semantic Search: {'PASS' if q2_pass else 'FAIL'}")
    print(f"   Noise Filtering: {'PASS' if q3_pass else 'FAIL'}")
    print(f"   Out-of-Domain Safety: {'PASS' if q4_pass else 'FAIL'}")
    print(f"   User Data Isolation: {'PASS' if user_isolation_pass else 'CRITICAL FAIL'}")
    print("--------------------------------------------------\n")


if __name__ == "__main__":
    asyncio.run(run_hybrid_retrieval_eval())

