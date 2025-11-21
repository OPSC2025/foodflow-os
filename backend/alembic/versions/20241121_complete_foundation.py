"""Complete foundation schema

Revision ID: 002_foundation
Revises: 001_initial
Create Date: 2024-11-21 10:00:00.000000

This migration includes:
- Tenants table
- Users, Roles, Permissions (Identity context)
- AI Telemetry tables (CopilotInteraction, AISuggestion, AIFeedback, WorkspaceAnalytics)
- PlantOps tables (already in 001_initial but ensuring they're complete)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002_foundation'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create foundation tables."""
    
    # Tenants table (if not exists from tenancy module)
    # This is created in the public schema
    op.execute("""
        CREATE TABLE IF NOT EXISTS tenants (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(255) NOT NULL,
            slug VARCHAR(100) NOT NULL UNIQUE,
            schema_name VARCHAR(100) NOT NULL UNIQUE,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            settings JSONB,
            subscription_tier VARCHAR(50),
            subscription_expires_at TIMESTAMP WITH TIME ZONE,
            contact_email VARCHAR(255),
            contact_name VARCHAR(255),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        )
    """)
    op.create_index('ix_tenants_slug', 'tenants', ['slug'], unique=True, if_not_exists=True)
    op.create_index('ix_tenants_is_active', 'tenants', ['is_active'], if_not_exists=True)
    
    # Permissions table (global, in public schema)
    op.execute("""
        CREATE TABLE IF NOT EXISTS permissions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(100) NOT NULL UNIQUE,
            resource VARCHAR(100) NOT NULL,
            action VARCHAR(50) NOT NULL,
            description VARCHAR(500),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        )
    """)
    op.create_index('ix_permissions_name', 'permissions', ['name'], unique=True, if_not_exists=True)
    
    # Roles table (tenant-specific, in public schema with tenant_id)
    op.execute("""
        CREATE TABLE IF NOT EXISTS roles (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            name VARCHAR(100) NOT NULL,
            description VARCHAR(500),
            is_system BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            UNIQUE (tenant_id, name)
        )
    """)
    op.create_index('ix_roles_tenant_id', 'roles', ['tenant_id'], if_not_exists=True)
    
    # Users table (tenant-specific)
    op.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            email VARCHAR(255) NOT NULL,
            hashed_password VARCHAR(255) NOT NULL,
            full_name VARCHAR(255),
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
            is_verified BOOLEAN NOT NULL DEFAULT FALSE,
            last_login_at TIMESTAMP WITH TIME ZONE,
            failed_login_attempts INTEGER NOT NULL DEFAULT 0,
            locked_until TIMESTAMP WITH TIME ZONE,
            reset_token VARCHAR(255),
            reset_token_expires_at TIMESTAMP WITH TIME ZONE,
            verification_token VARCHAR(255),
            verification_token_expires_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            UNIQUE (tenant_id, email)
        )
    """)
    op.create_index('ix_users_tenant_id', 'users', ['tenant_id'], if_not_exists=True)
    op.create_index('ix_users_email', 'users', ['email'], if_not_exists=True)
    
    # User-Role association table
    op.execute("""
        CREATE TABLE IF NOT EXISTS user_roles (
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
            PRIMARY KEY (user_id, role_id)
        )
    """)
    
    # Role-Permission association table
    op.execute("""
        CREATE TABLE IF NOT EXISTS role_permissions (
            role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
            permission_id UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
            PRIMARY KEY (role_id, permission_id)
        )
    """)
    
    # Refresh tokens table
    op.execute("""
        CREATE TABLE IF NOT EXISTS refresh_tokens (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            token VARCHAR(500) NOT NULL UNIQUE,
            expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
            is_revoked BOOLEAN NOT NULL DEFAULT FALSE,
            revoked_at TIMESTAMP WITH TIME ZONE,
            device_info VARCHAR(500),
            ip_address VARCHAR(45),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        )
    """)
    op.create_index('ix_refresh_tokens_user_id', 'refresh_tokens', ['user_id'], if_not_exists=True)
    op.create_index('ix_refresh_tokens_token', 'refresh_tokens', ['token'], unique=True, if_not_exists=True)
    
    # AI Telemetry tables
    
    # Copilot interactions
    op.execute("""
        CREATE TABLE IF NOT EXISTS copilot_interactions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            user_id UUID REFERENCES users(id) ON DELETE SET NULL,
            workspace VARCHAR(50) NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            tools_used JSONB,
            tokens_used INTEGER,
            duration_ms INTEGER,
            feedback_score INTEGER,
            feedback_comment TEXT,
            feedback_at TIMESTAMP WITH TIME ZONE,
            metadata JSONB,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        )
    """)
    op.create_index('ix_copilot_interactions_tenant_id', 'copilot_interactions', ['tenant_id'], if_not_exists=True)
    op.create_index('ix_copilot_interactions_user_id', 'copilot_interactions', ['user_id'], if_not_exists=True)
    op.create_index('ix_copilot_interactions_workspace', 'copilot_interactions', ['workspace'], if_not_exists=True)
    op.create_index('ix_copilot_interactions_created_at', 'copilot_interactions', ['created_at'], if_not_exists=True)
    
    # AI suggestions
    op.execute("""
        CREATE TABLE IF NOT EXISTS ai_suggestions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            interaction_id UUID REFERENCES copilot_interactions(id) ON DELETE SET NULL,
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            user_id UUID REFERENCES users(id) ON DELETE SET NULL,
            suggestion_type VARCHAR(100) NOT NULL,
            suggestion_text TEXT NOT NULL,
            payload JSONB NOT NULL,
            applied_flag BOOLEAN NOT NULL DEFAULT FALSE,
            applied_at TIMESTAMP WITH TIME ZONE,
            applied_by UUID REFERENCES users(id) ON DELETE SET NULL,
            before_metrics JSONB,
            after_metrics JSONB,
            estimated_impact JSONB,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        )
    """)
    op.create_index('ix_ai_suggestions_tenant_id', 'ai_suggestions', ['tenant_id'], if_not_exists=True)
    op.create_index('ix_ai_suggestions_suggestion_type', 'ai_suggestions', ['suggestion_type'], if_not_exists=True)
    op.create_index('ix_ai_suggestions_applied_flag', 'ai_suggestions', ['applied_flag'], if_not_exists=True)
    
    # AI feedback
    op.execute("""
        CREATE TABLE IF NOT EXISTS ai_feedback (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            interaction_id UUID NOT NULL REFERENCES copilot_interactions(id) ON DELETE CASCADE,
            rating INTEGER NOT NULL,
            comment TEXT,
            is_accurate BOOLEAN,
            is_helpful BOOLEAN,
            is_timely BOOLEAN,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        )
    """)
    op.create_index('ix_ai_feedback_interaction_id', 'ai_feedback', ['interaction_id'], if_not_exists=True)
    
    # Workspace analytics
    op.execute("""
        CREATE TABLE IF NOT EXISTS workspace_analytics (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            workspace VARCHAR(50) NOT NULL,
            date TIMESTAMP WITH TIME ZONE NOT NULL,
            total_interactions INTEGER NOT NULL DEFAULT 0,
            unique_users INTEGER NOT NULL DEFAULT 0,
            avg_response_time_ms REAL,
            avg_tokens_used REAL,
            tool_usage JSONB,
            avg_feedback_score REAL,
            feedback_count INTEGER NOT NULL DEFAULT 0,
            suggestions_made INTEGER NOT NULL DEFAULT 0,
            suggestions_applied INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        )
    """)
    op.create_index('ix_workspace_analytics_tenant_id', 'workspace_analytics', ['tenant_id'], if_not_exists=True)
    op.create_index('ix_workspace_analytics_workspace', 'workspace_analytics', ['workspace'], if_not_exists=True)
    op.create_index('ix_workspace_analytics_date', 'workspace_analytics', ['date'], if_not_exists=True)
    
    # Outbox events table (for transactional outbox pattern)
    op.execute("""
        CREATE TABLE IF NOT EXISTS outbox_events (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            event_type VARCHAR(255) NOT NULL,
            aggregate_type VARCHAR(100) NOT NULL,
            aggregate_id UUID NOT NULL,
            payload JSONB NOT NULL,
            metadata JSONB,
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            published_at TIMESTAMP WITH TIME ZONE,
            error_message TEXT,
            retry_count VARCHAR(20) NOT NULL DEFAULT '0',
            occurred_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        )
    """)
    op.create_index('ix_outbox_events_tenant_id', 'outbox_events', ['tenant_id'], if_not_exists=True)
    op.create_index('ix_outbox_events_status', 'outbox_events', ['status'], if_not_exists=True)
    op.create_index('ix_outbox_events_created_at', 'outbox_events', ['created_at'], if_not_exists=True)


def downgrade() -> None:
    """Drop foundation tables."""
    
    # Drop in reverse order to respect foreign keys
    op.drop_table('outbox_events')
    op.drop_table('workspace_analytics')
    op.drop_table('ai_feedback')
    op.drop_table('ai_suggestions')
    op.drop_table('copilot_interactions')
    op.drop_table('refresh_tokens')
    op.drop_table('role_permissions')
    op.drop_table('user_roles')
    op.drop_table('users')
    op.drop_table('roles')
    op.drop_table('permissions')
    op.drop_table('tenants')

