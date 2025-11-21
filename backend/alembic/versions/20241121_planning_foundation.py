"""Planning foundation tables

Revision ID: 20241121_planning_foundation
Revises: 20241121_fsq_foundation
Create Date: 2024-11-21
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20241121_planning_foundation"
down_revision: Union[str, None] = "20241121_fsq_foundation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create Planning & Supply foundation tables:
    - forecasts
    - production_plans
    - safety_stocks
    - inventory_levels
    """
    
    # Forecasts table
    op.create_table(
        "forecasts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("version", sa.String(50), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("sku_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("method", sa.String(50), nullable=False, server_default="ai_ml"),
        sa.Column("forecast_data", postgresql.JSONB, nullable=False),
        sa.Column("accuracy_metrics", postgresql.JSONB, nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("generated_by_ai", sa.Boolean(), default=False, nullable=False),
        sa.Column("ai_model_version", sa.String(100), nullable=True),
        sa.Column("ai_suggestion_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("parent_forecast_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.Column("approved_by", sa.String(255), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["parent_forecast_id"], ["forecasts.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_forecasts_tenant_id", "forecasts", ["tenant_id"])
    op.create_index("ix_forecasts_product_id", "forecasts", ["product_id"])
    op.create_index("ix_forecasts_sku_id", "forecasts", ["sku_id"])
    op.create_index("ix_forecasts_status", "forecasts", ["status"])
    
    # Production Plans table
    op.create_table(
        "production_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plan_name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("forecast_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("line_ids", postgresql.JSONB, nullable=True),
        sa.Column("plan_data", postgresql.JSONB, nullable=False),
        sa.Column("capacity_analysis", postgresql.JSONB, nullable=True),
        sa.Column("constraints", postgresql.JSONB, nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("generated_by_ai", sa.Boolean(), default=False, nullable=False),
        sa.Column("ai_optimizations", postgresql.JSONB, nullable=True),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.Column("approved_by", sa.String(255), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("execution_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("execution_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completion_percentage", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["forecast_id"], ["forecasts.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_production_plans_tenant_id", "production_plans", ["tenant_id"])
    op.create_index("ix_production_plans_status", "production_plans", ["status"])
    op.create_index("ix_production_plans_forecast_id", "production_plans", ["forecast_id"])
    
    # Safety Stocks table
    op.create_table(
        "safety_stocks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("sku_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ingredient_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("plant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("warehouse_location", sa.String(255), nullable=True),
        sa.Column("policy", sa.String(50), nullable=False, server_default="service_level"),
        sa.Column("safety_stock_quantity", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(50), nullable=False, server_default="units"),
        sa.Column("target_service_level", sa.Float(), nullable=True),
        sa.Column("lead_time_days", sa.Float(), nullable=True),
        sa.Column("demand_std_dev", sa.Float(), nullable=True),
        sa.Column("demand_mean", sa.Float(), nullable=True),
        sa.Column("reorder_point", sa.Float(), nullable=True),
        sa.Column("calculation_details", postgresql.JSONB, nullable=True),
        sa.Column("calculated_by_ai", sa.Boolean(), default=False, nullable=False),
        sa.Column("ai_confidence", sa.Float(), nullable=True),
        sa.Column("ai_reasoning", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column("last_reviewed", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_review_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.text("now()"), nullable=True),
    )
    op.create_index("ix_safety_stocks_tenant_id", "safety_stocks", ["tenant_id"])
    op.create_index("ix_safety_stocks_product_id", "safety_stocks", ["product_id"])
    op.create_index("ix_safety_stocks_sku_id", "safety_stocks", ["sku_id"])
    op.create_index("ix_safety_stocks_ingredient_id", "safety_stocks", ["ingredient_id"])
    
    # Inventory Levels table
    op.create_table(
        "inventory_levels",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("sku_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ingredient_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("plant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("warehouse_location", sa.String(255), nullable=True),
        sa.Column("on_hand_quantity", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("available_quantity", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("allocated_quantity", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("in_transit_quantity", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("unit", sa.String(50), nullable=False, server_default="units"),
        sa.Column("is_below_safety_stock", sa.Boolean(), default=False, nullable=False),
        sa.Column("is_stockout", sa.Boolean(), default=False, nullable=False),
        sa.Column("days_of_supply", sa.Float(), nullable=True),
        sa.Column("last_movement_type", sa.String(50), nullable=True),
        sa.Column("last_movement_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_movement_quantity", sa.Float(), nullable=True),
        sa.Column("as_of_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.text("now()"), nullable=True),
    )
    op.create_index("ix_inventory_levels_tenant_id", "inventory_levels", ["tenant_id"])
    op.create_index("ix_inventory_levels_product_id", "inventory_levels", ["product_id"])
    op.create_index("ix_inventory_levels_sku_id", "inventory_levels", ["sku_id"])
    op.create_index("ix_inventory_levels_ingredient_id", "inventory_levels", ["ingredient_id"])
    op.create_index("ix_inventory_levels_warehouse", "inventory_levels", ["warehouse_location"])


def downgrade() -> None:
    """Drop all Planning tables."""
    op.drop_table("inventory_levels")
    op.drop_table("safety_stocks")
    op.drop_table("production_plans")
    op.drop_table("forecasts")

