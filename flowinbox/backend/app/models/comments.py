import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import String, Text, ForeignKey, DateTime, JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base



class ThreadComment(Base):
    """Thread-level comments (human notes or structured AI agent receipts)."""
    __tablename__ = "thread_comments"

    thread_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("email_threads.id", ondelete="CASCADE"), index=True, nullable=False)
    author_type: Mapped[str] = mapped_column(String(20), default="human", nullable=False)  # 'human' or 'agent'
    author_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    author_name: Mapped[str] = mapped_column(String(100), default="User", nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    structured_payload: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
