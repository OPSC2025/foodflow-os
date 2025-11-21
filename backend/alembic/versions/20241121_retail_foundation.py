"""Retail foundation tables

Revision ID: 20241121_retail_foundation
Revises: 20241121_brand_foundation
Create Date: 2024-11-21
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20241121_retail_foundation"
down_revision: Union[str, None] = "20241121_brand_foundation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create Retail foundation tables:
    - banners
    - stores
    - categories
    - pos_transactions
    - waste
    - osa_events
    - promos
    """
    
    # Banners table
    op.create_table(
        "banners",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("parent_company", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.text("now()"), nullable=True),
    )
    op.create_index("ix_banners_tenant_id", "banners", ["tenant_id"])
    op.create_index("ix_banners_code", "banners", ["code"])
    
    # Stores table
    op.create_table(
        "stores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("banner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("store_number", sa.String(50), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("store_format", sa.String(100), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("state", sa.String(100), nullable=True),
        sa.Column("country", sa.String(100), nullable=True),
        sa.Column("postal_code", sa.String(20), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("square_footage", sa.Integer(), nullable=True),
        sa.Column("opening_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("manager_name", sa.String(255), nullable=True),
        sa.Column("manager_email", sa.String(255), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["banner_id"], ["banners.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_stores_tenant_id", "stores", ["tenant_id"])
    op.create_index("ix_stores_banner_id", "stores", ["banner_id"])
    op.create_index("ix_stores_store_number", "stores", ["store_number"])
    
    # Categories table
    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("parent_category_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["parent_category_id"], ["categories.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_categories_tenant_id", "categories", ["tenant_id"])
    op.create_index("ix_categories_code", "categories", ["code"])
    
    # Promos table (create before pos_transactions)
    op.create_table(
        "promos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("promo_name", sa.String(255), nullable=False),
        sa.Column("promo_code", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("promo_type", sa.String(50), nullable=False),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("banner_ids", postgresql.JSONB, nullable=True),
        sa.Column("store_ids", postgresql.JSONB, nullable=True),
        sa.Column("product_ids", postgresql.JSONB, nullable=True),
        sa.Column("sku_ids", postgresql.JSONB, nullable=True),
        sa.Column("discount_percentage", sa.Float(), nullable=True),
        sa.Column("discount_amount", sa.Float(), nullable=True),
        sa.Column("promo_mechanics", postgresql.JSONB, nullable=True),
        sa.Column("budget", sa.Float(), nullable=True),
        sa.Column("target_units", sa.Integer(), nullable=True),
        sa.Column("target_revenue", sa.Float(), nullable=True),
        sa.Column("actual_units_sold", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("actual_revenue", sa.Float(), nullable=True, server_default="0.0"),
        sa.Column("actual_discount_given", sa.Float(), nullable=True, server_default="0.0"),
        sa.Column("roi", sa.Float(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="planned"),
        sa.Column("suggested_by_ai", sa.Boolean(), default=False, nullable=False),
        sa.Column("ai_confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.text("now()"), nullable=True),
    )
    op.create_index("ix_promos_tenant_id", "promos", ["tenant_id"])
    op.create_index("ix_promos_code", "promos", ["promo_code"])
    op.create_index("ix_promos_type", "promos", ["promo_type"])
    op.create_index("ix_promos_start_date", "promos", ["start_date"])
    op.create_index("ix_promos_end_date", "promos", ["end_date"])
    
    # POS Transactions table
    op.create_table(
        "pos_transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("transaction_id", sa.String(100), nullable=False),
        sa.Column("transaction_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sku_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("upc", sa.String(50), nullable=True),
        sa.Column("external_sku_id", sa.String(100), nullable=True),
        sa.Column("product_name", sa.String(255), nullable=True),
        sa.Column("quantity_sold", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Float(), nullable=False),
        sa.Column("total_amount", sa.Float(), nullable=False),
        sa.Column("discount_amount", sa.Float(), nullable=True, server_default="0.0"),
        sa.Column("net_amount", sa.Float(), nullable=False),
        sa.Column("promo_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["promo_id"], ["promos.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_pos_transactions_tenant_id", "pos_transactions", ["tenant_id"])
    op.create_index("ix_pos_transactions_store_id", "pos_transactions", ["store_id"])
    op.create_index("ix_pos_transactions_transaction_id", "pos_transactions", ["transaction_id"])
    op.create_index("ix_pos_transactions_date", "pos_transactions", ["transaction_date"])
    op.create_index("ix_pos_transactions_sku_id", "pos_transactions", ["sku_id"])
    op.create_index("ix_pos_transactions_product_id", "pos_transactions", ["product_id"])
    op.create_index("ix_pos_transactions_upc", "pos_transactions", ["upc"])
    
    # Waste table
    op.create_table(
        "waste",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recorded_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sku_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("product_name", sa.String(255), nullable=True),
        sa.Column("quantity_wasted", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(50), nullable=False, server_default="units"),
        sa.Column("estimated_value", sa.Float(), nullable=True),
        sa.Column("reason", sa.String(50), nullable=False),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("recorded_by", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_waste_tenant_id", "waste", ["tenant_id"])
    op.create_index("ix_waste_store_id", "waste", ["store_id"])
    op.create_index("ix_waste_recorded_date", "waste", ["recorded_date"])
    op.create_index("ix_waste_sku_id", "waste", ["sku_id"])
    op.create_index("ix_waste_product_id", "waste", ["product_id"])
    op.create_index("ix_waste_reason", "waste", ["reason"])
    
    # OSA Events table
    op.create_table(
        "osa_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("detected_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sku_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("product_name", sa.String(255), nullable=True),
        sa.Column("osa_status", sa.String(50), nullable=False),
        sa.Column("issue_type", sa.String(50), nullable=False),
        sa.Column("on_hand_quantity", sa.Integer(), nullable=True),
        sa.Column("backroom_quantity", sa.Integer(), nullable=True),
        sa.Column("shelf_capacity", sa.Integer(), nullable=True),
        sa.Column("resolved", sa.Boolean(), default=False, nullable=False),
        sa.Column("resolved_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("estimated_lost_sales", sa.Float(), nullable=True),
        sa.Column("duration_hours", sa.Float(), nullable=True),
        sa.Column("detected_by", sa.String(100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_osa_events_tenant_id", "osa_events", ["tenant_id"])
    op.create_index("ix_osa_events_store_id", "osa_events", ["store_id"])
    op.create_index("ix_osa_events_detected_date", "osa_events", ["detected_date"])
    op.create_index("ix_osa_events_sku_id", "osa_events", ["sku_id"])
    op.create_index("ix_osa_events_product_id", "osa_events", ["product_id"])
    op.create_index("ix_osa_events_osa_status", "osa_events", ["osa_status"])


def downgrade() -> None:
    """Drop all Retail tables."""
    op.drop_table("osa_events")
    op.drop_table("waste")
    op.drop_table("pos_transactions")
    op.drop_table("promos")
    op.drop_table("categories")
    op.drop_table("stores")
    op.drop_table("banners")

