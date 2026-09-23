"""009_workspace_invitations

Revision ID: 009_workspace_invitations
Revises: 008_sync_missing_columns_and_channel_types
Create Date: 2026-09-23 16:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '009_workspace_invitations'
down_revision: Union[str, None] = '008_sync_missing_columns_and_channel_types'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if 'workspace_invitations' not in tables:
        op.create_table(
            'workspace_invitations',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('workspace_id', sa.UUID(), nullable=False),
            sa.Column('email', sa.String(length=255), nullable=False),
            sa.Column('role', sa.String(length=50), server_default='MEMBER', nullable=False),
            sa.Column('token_hash', sa.String(length=128), nullable=False),
            sa.Column('invited_by', sa.UUID(), nullable=False),
            sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(['invited_by'], ['users.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_workspace_invitations_token_hash', 'workspace_invitations', ['token_hash'], unique=True)
        op.create_index('ix_workspace_invitations_workspace_id', 'workspace_invitations', ['workspace_id'], unique=False)
        op.create_index('ix_workspace_invitations_email', 'workspace_invitations', ['email'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_workspace_invitations_email', table_name='workspace_invitations')
    op.drop_index('ix_workspace_invitations_workspace_id', table_name='workspace_invitations')
    op.drop_index('ix_workspace_invitations_token_hash', table_name='workspace_invitations')
    op.drop_table('workspace_invitations')
