"""copilot conversations

Revision ID: 20241121_copilot
Revises: 20241121_retail_foundation
Create Date: 2024-11-21 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20241121_copilot'
down_revision: Union[str, None] = '20241121_retail_foundation'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create copilot_conversations table
    op.create_table(
        'copilot_conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workspace', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Create indexes for copilot_conversations
    op.create_index('ix_copilot_conversations_tenant_id', 'copilot_conversations', ['tenant_id'])
    op.create_index('ix_copilot_conversations_user_id', 'copilot_conversations', ['user_id'])
    op.create_index('ix_copilot_conversations_workspace', 'copilot_conversations', ['workspace'])
    op.create_index('ix_copilot_conversations_tenant_user', 'copilot_conversations', ['tenant_id', 'user_id'])
    op.create_index('ix_copilot_conversations_tenant_workspace', 'copilot_conversations', ['tenant_id', 'workspace'])
    
    # Create copilot_messages table
    op.create_table(
        'copilot_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('tools_used', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('tokens_used', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('function_call', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['copilot_conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Create indexes for copilot_messages
    op.create_index('ix_copilot_messages_conversation_id', 'copilot_messages', ['conversation_id'])
    op.create_index('ix_copilot_messages_created_at', 'copilot_messages', ['created_at'])
    op.create_index('ix_copilot_messages_conversation_created', 'copilot_messages', ['conversation_id', 'created_at'])


def downgrade() -> None:
    # Drop copilot_messages table and indexes
    op.drop_index('ix_copilot_messages_conversation_created', table_name='copilot_messages')
    op.drop_index('ix_copilot_messages_created_at', table_name='copilot_messages')
    op.drop_index('ix_copilot_messages_conversation_id', table_name='copilot_messages')
    op.drop_table('copilot_messages')
    
    # Drop copilot_conversations table and indexes
    op.drop_index('ix_copilot_conversations_tenant_workspace', table_name='copilot_conversations')
    op.drop_index('ix_copilot_conversations_tenant_user', table_name='copilot_conversations')
    op.drop_index('ix_copilot_conversations_workspace', table_name='copilot_conversations')
    op.drop_index('ix_copilot_conversations_user_id', table_name='copilot_conversations')
    op.drop_index('ix_copilot_conversations_tenant_id', table_name='copilot_conversations')
    op.drop_table('copilot_conversations')

