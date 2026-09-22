"""008_sync_missing_columns_and_channel_types

Revision ID: 008_sync_missing_columns_and_channel_types
Revises: 007_comments_and_finance
Create Date: 2026-09-17 16:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '008_sync_missing_columns_and_channel_types'
down_revision: Union[str, None] = '007_comments_and_finance'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # 1. Add missing updated_at to channel_messages
    cm_cols = [c['name'] for c in inspector.get_columns('channel_messages')]
    if 'updated_at' not in cm_cols:
        op.add_column('channel_messages', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))

    # 2. Add missing created_at and updated_at to channel_memberships
    mem_cols = [c['name'] for c in inspector.get_columns('channel_memberships')]
    if 'created_at' not in mem_cols:
        op.add_column('channel_memberships', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    if 'updated_at' not in mem_cols:
        op.add_column('channel_memberships', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))

    # 3. Add missing updated_at to channel_attachments
    att_cols = [c['name'] for c in inspector.get_columns('channel_attachments')]
    if 'updated_at' not in att_cols:
        op.add_column('channel_attachments', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))



def downgrade() -> None:
    op.drop_column('channel_attachments', 'updated_at')
    op.drop_column('channel_memberships', 'updated_at')
    op.drop_column('channel_memberships', 'created_at')
    op.drop_column('channel_messages', 'updated_at')
