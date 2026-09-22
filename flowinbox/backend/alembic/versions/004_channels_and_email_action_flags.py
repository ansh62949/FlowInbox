"""004_channels_and_email_action_flags

Revision ID: 004_channels_and_email_action_flags
Revises: 003_channel_messages_and_tokens
Create Date: 2026-09-17 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '004_channels_and_email_action_flags'
down_revision: Union[str, None] = '003_channel_messages_and_tokens'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. channel_filter_rules table
    op.create_table(
        'channel_filter_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('channel_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('field', sa.String(length=50), nullable=False),
        sa.Column('value', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['channel_id'], ['channels.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_channel_filter_rules_channel_id'), 'channel_filter_rules', ['channel_id'], unique=False)

    # 2. Add onboarding_completed_at to users
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('onboarding_completed_at', sa.DateTime(timezone=True), nullable=True))

    # 3. Add email action & folder flags to email_threads
    with op.batch_alter_table('email_threads') as batch_op:
        batch_op.add_column(sa.Column('channel_id', postgresql.UUID(as_uuid=True), nullable=True))
        batch_op.create_foreign_key('fk_email_threads_channel_id', 'channels', ['channel_id'], ['id'], ondelete='SET NULL')
        batch_op.add_column(sa.Column('folder', sa.String(length=50), server_default='inbox', nullable=False))
        batch_op.create_index('ix_email_threads_folder', ['folder'], unique=False)
        batch_op.add_column(sa.Column('is_starred', sa.Boolean(), server_default='false', nullable=False))
        batch_op.create_index('ix_email_threads_is_starred', ['is_starred'], unique=False)
        batch_op.add_column(sa.Column('is_read', sa.Boolean(), server_default='true', nullable=False))
        batch_op.create_index('ix_email_threads_is_read', ['is_read'], unique=False)
        batch_op.add_column(sa.Column('is_archived', sa.Boolean(), server_default='false', nullable=False))
        batch_op.create_index('ix_email_threads_is_archived', ['is_archived'], unique=False)
        batch_op.add_column(sa.Column('is_trashed', sa.Boolean(), server_default='false', nullable=False))
        batch_op.create_index('ix_email_threads_is_trashed', ['is_trashed'], unique=False)
        batch_op.add_column(sa.Column('is_snoozed', sa.Boolean(), server_default='false', nullable=False))
        batch_op.create_index('ix_email_threads_is_snoozed', ['is_snoozed'], unique=False)
        batch_op.add_column(sa.Column('snoozed_until', sa.DateTime(timezone=True), nullable=True))

    # 4. api_tokens table
    op.create_table(
        'api_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('token_hash', sa.String(length=128), nullable=False),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_api_tokens_token_hash'), 'api_tokens', ['token_hash'], unique=True)
    op.create_index(op.f('ix_api_tokens_user_id'), 'api_tokens', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_table('api_tokens')

    op.drop_column('email_threads', 'snoozed_until')
    op.drop_index(op.f('ix_email_threads_is_snoozed'), table_name='email_threads')
    op.drop_column('email_threads', 'is_snoozed')
    op.drop_index(op.f('ix_email_threads_is_trashed'), table_name='email_threads')
    op.drop_column('email_threads', 'is_trashed')
    op.drop_index(op.f('ix_email_threads_is_archived'), table_name='email_threads')
    op.drop_column('email_threads', 'is_archived')
    op.drop_index(op.f('ix_email_threads_is_read'), table_name='email_threads')
    op.drop_column('email_threads', 'is_read')
    op.drop_index(op.f('ix_email_threads_is_starred'), table_name='email_threads')
    op.drop_column('email_threads', 'is_starred')
    op.drop_index(op.f('ix_email_threads_folder'), table_name='email_threads')
    op.drop_column('email_threads', 'folder')
    op.drop_constraint('fk_email_threads_channel_id', 'email_threads', type_='foreignkey')
    op.drop_column('email_threads', 'channel_id')

    op.drop_column('users', 'onboarding_completed_at')

    op.drop_table('channel_filter_rules')
