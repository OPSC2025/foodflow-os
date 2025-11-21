"""PlantOps expansion: add Trial, Downtime, and MoneyLeak models

Revision ID: 20241121_plantops_expansion
Revises: 20241121_complete_foundation
Create Date: 2024-11-21 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20241121_plantops_expansion'
down_revision: Union[str, None] = '20241121_complete_foundation'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create trials table
    op.create_table(
        'trials',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('trial_number', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('line_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('product_code', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='planned'),
        sa.Column('planned_start_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('planned_end_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('actual_start_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('actual_end_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('parameters', sa.Text(), nullable=True),
        sa.Column('expected_outcome', sa.Text(), nullable=True),
        sa.Column('success_criteria', sa.Text(), nullable=True),
        sa.Column('results', sa.Text(), nullable=True),
        sa.Column('was_successful', sa.Boolean(), nullable=True),
        sa.Column('batch_ids', sa.Text(), nullable=True),
        sa.Column('observations', sa.Text(), nullable=True),
        sa.Column('learnings', sa.Text(), nullable=True),
        sa.Column('recommendations', sa.Text(), nullable=True),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('owner_name', sa.String(length=255), nullable=True),
        sa.Column('suggested_by_ai', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('ai_suggestion_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('metadata', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['line_id'], ['production_lines.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_trials_tenant_trial_number', 'trials', ['tenant_id', 'trial_number'], unique=True)
    op.create_index('ix_trials_line_status', 'trials', ['line_id', 'status'])
    op.create_index('ix_trials_status_start', 'trials', ['tenant_id', 'status', 'actual_start_time'])

    # Create downtimes table
    op.create_table(
        'downtimes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('line_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('batch_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_minutes', sa.Numeric(10, 2), nullable=True),
        sa.Column('reason_category', sa.String(length=100), nullable=False),
        sa.Column('reason_detail', sa.String(length=255), nullable=True),
        sa.Column('is_planned', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('root_cause', sa.Text(), nullable=True),
        sa.Column('resolution', sa.Text(), nullable=True),
        sa.Column('preventive_action', sa.Text(), nullable=True),
        sa.Column('units_lost', sa.Numeric(12, 2), nullable=True),
        sa.Column('cost_impact', sa.Numeric(12, 2), nullable=True),
        sa.Column('reported_by', sa.String(length=255), nullable=True),
        sa.Column('resolved_by', sa.String(length=255), nullable=True),
        sa.Column('response_time_minutes', sa.Numeric(10, 2), nullable=True),
        sa.Column('metadata', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['line_id'], ['production_lines.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['batch_id'], ['production_batches.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_downtimes_tenant_line_time', 'downtimes', ['tenant_id', 'line_id', 'start_time'])
    op.create_index('ix_downtimes_reason_time', 'downtimes', ['reason_category', 'start_time'])
    op.create_index('ix_downtimes_is_planned', 'downtimes', ['tenant_id', 'is_planned', 'start_time'])

    # Create money_leaks table
    op.create_table(
        'money_leaks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('line_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('plant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('batch_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('subcategory', sa.String(length=100), nullable=True),
        sa.Column('amount_usd', sa.Numeric(12, 2), nullable=False),
        sa.Column('quantity_lost', sa.Numeric(12, 2), nullable=True),
        sa.Column('unit_cost', sa.Numeric(12, 2), nullable=True),
        sa.Column('time_lost_minutes', sa.Numeric(10, 2), nullable=True),
        sa.Column('hourly_cost', sa.Numeric(12, 2), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('root_cause', sa.Text(), nullable=True),
        sa.Column('is_avoidable', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('action_taken', sa.Text(), nullable=True),
        sa.Column('calculation_method', sa.String(length=255), nullable=True),
        sa.Column('metadata', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['line_id'], ['production_lines.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['batch_id'], ['production_batches.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_money_leaks_tenant_period', 'money_leaks', ['tenant_id', 'period_start', 'period_end'])
    op.create_index('ix_money_leaks_category_period', 'money_leaks', ['category', 'period_start'])
    op.create_index('ix_money_leaks_line_period', 'money_leaks', ['line_id', 'period_start'])


def downgrade() -> None:
    # Drop money_leaks table
    op.drop_index('ix_money_leaks_line_period', table_name='money_leaks')
    op.drop_index('ix_money_leaks_category_period', table_name='money_leaks')
    op.drop_index('ix_money_leaks_tenant_period', table_name='money_leaks')
    op.drop_table('money_leaks')

    # Drop downtimes table
    op.drop_index('ix_downtimes_is_planned', table_name='downtimes')
    op.drop_index('ix_downtimes_reason_time', table_name='downtimes')
    op.drop_index('ix_downtimes_tenant_line_time', table_name='downtimes')
    op.drop_table('downtimes')

    # Drop trials table
    op.drop_index('ix_trials_status_start', table_name='trials')
    op.drop_index('ix_trials_line_status', table_name='trials')
    op.drop_index('ix_trials_tenant_trial_number', table_name='trials')
    op.drop_table('trials')

