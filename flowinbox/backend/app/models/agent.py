import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, ForeignKey, DateTime, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, GUID


class AgentRun(Base):
    """Execution run of the LangGraph agent for a user request."""
    __tablename__ = "agent_runs"

    user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    request_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="running", nullable=False)  # running, waiting_approval, completed, failed
    intent: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    plan: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    final_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class ToolCall(Base):
    """Specific tool invocation record within an agent run."""
    __tablename__ = "tool_calls"

    agent_run_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("agent_runs.id", ondelete="CASCADE"), index=True, nullable=False)
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    input_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    output_payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="success", nullable=False)  # success, error
    latency_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class Approval(Base):
    """Pending human approval for consequential agent actions (send email, create event)."""
    __tablename__ = "approvals"

    user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    agent_run_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("agent_runs.id", ondelete="CASCADE"), index=True, nullable=False)
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)  # send_email, create_event, update_event
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)  # Full exact payload to execute
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True, nullable=False)  # pending, approved, rejected, expired
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class AuditLog(Base):
    """Human-readable event trail per agent run for client activity view."""
    __tablename__ = "audit_logs"

    user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    agent_run_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("agent_runs.id", ondelete="CASCADE"), index=True, nullable=False)
    step_description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="info", nullable=False)  # info, warning, success, error


class UserPreference(Base):
    """Custom user preferences (e.g., tone, notification settings)."""
    __tablename__ = "user_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    email_summary_frequency: Mapped[str] = mapped_column(String(50), default="daily", nullable=False)
    preferred_tone: Mapped[str] = mapped_column(String(50), default="professional", nullable=False)
    custom_instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class WritingProfile(Base):
    """Derived writing-style profile based on user's past sent emails."""
    __tablename__ = "writing_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    formality_level: Mapped[str] = mapped_column(String(50), default="neutral", nullable=False)
    avg_sentence_length: Mapped[str] = mapped_column(String(50), default="medium", nullable=False)
    common_greetings: Mapped[dict] = mapped_column(JSON, default=list, nullable=False)
    common_signoffs: Mapped[dict] = mapped_column(JSON, default=list, nullable=False)
    recurring_phrases: Mapped[dict] = mapped_column(JSON, default=list, nullable=False)
    sample_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class EvaluationRun(Base):
    """Retrieval and agent benchmark evaluation run results."""
    __tablename__ = "evaluation_runs"

    metrics: Mapped[dict] = mapped_column(JSON, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)

