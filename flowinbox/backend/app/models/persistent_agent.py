import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, GUID


class AgentEntity(Base):
    """Persistent AI Agent definition in a workspace."""
    __tablename__ = "agents"

    workspace_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    type: Mapped[str] = mapped_column(String(50), default="triage", nullable=False)  # triage, receipt_matcher, meeting_assistant, followup
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)  # active, paused, disabled
    system_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    permissions: Mapped[List["AgentPermission"]] = relationship("AgentPermission", back_populates="agent", cascade="all, delete-orphan")
    channel_access: Mapped[List["AgentChannelAccess"]] = relationship("AgentChannelAccess", back_populates="agent", cascade="all, delete-orphan")


class AgentPermission(Base):
    """Specific permission / tool access rule for an AI agent."""
    __tablename__ = "agent_permissions"

    agent_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("agents.id", ondelete="CASCADE"), index=True, nullable=False)
    permission: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., 'read_emails', 'create_drafts', 'send_email', 'get_events'
    allowed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    agent: Mapped["AgentEntity"] = relationship("AgentEntity", back_populates="permissions")


class AgentChannelAccess(Base):
    """Channel association for an AI agent."""
    __tablename__ = "agent_channel_access"

    agent_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("agents.id", ondelete="CASCADE"), index=True, nullable=False)
    channel_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("channels.id", ondelete="CASCADE"), index=True, nullable=False)

    agent: Mapped["AgentEntity"] = relationship("AgentEntity", back_populates="channel_access")

