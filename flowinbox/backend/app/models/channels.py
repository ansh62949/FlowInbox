import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, GUID


class Channel(Base):
    """Channel for auto-routing email threads and collaborative team conversations."""
    __tablename__ = "channels"

    user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    workspace_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default="hash")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    rules: Mapped[List["ChannelFilterRule"]] = relationship("ChannelFilterRule", back_populates="channel", cascade="all, delete-orphan")
    messages: Mapped[List["ChannelMessage"]] = relationship("ChannelMessage", back_populates="channel", cascade="all, delete-orphan")
    memberships: Mapped[List["ChannelMembership"]] = relationship("ChannelMembership", back_populates="channel", cascade="all, delete-orphan")


class ChannelFilterRule(Base):
    """Filter rule for routing threads into a channel."""
    __tablename__ = "channel_filter_rules"

    channel_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("channels.id", ondelete="CASCADE"), index=True, nullable=False)
    field: Mapped[str] = mapped_column(String(50), nullable=False)  # 'from', 'subject_contains', 'label'
    value: Mapped[str] = mapped_column(String(255), nullable=False)

    # Relationships
    channel: Mapped["Channel"] = relationship("Channel", back_populates="rules")


class ChannelMessage(Base):
    """Post or message within a collaborative channel (human or AI agent)."""
    __tablename__ = "channel_messages"

    channel_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("channels.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    sender_name: Mapped[str] = mapped_column(String(100), nullable=False)
    sender_type: Mapped[str] = mapped_column(String(20), nullable=False, default="human")  # 'human', 'agent', 'system'
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    thread_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), ForeignKey("email_threads.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    channel: Mapped["Channel"] = relationship("Channel", back_populates="messages")
    attachments: Mapped[List["ChannelAttachment"]] = relationship("ChannelAttachment", back_populates="message", cascade="all, delete-orphan")


class ChannelMembership(Base):
    """User membership in a workspace channel."""
    __tablename__ = "channel_memberships"

    channel_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("channels.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="member")
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    channel: Mapped["Channel"] = relationship("Channel", back_populates="memberships")


class ChannelAttachment(Base):
    """File attachment linked to a channel message."""
    __tablename__ = "channel_attachments"

    message_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("channel_messages.id", ondelete="CASCADE"), index=True, nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str] = mapped_column(String(512), nullable=False)
    file_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    message: Mapped["ChannelMessage"] = relationship("ChannelMessage", back_populates="attachments")


