"""Brand foundation tables

Revision ID: 20241121_brand_foundation
Revises: 20241121_planning_foundation
Create Date: 2024-11-21
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20241121_brand_foundation"
down_revision: Union[str, None] = "20241121_planning_foundation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create Brand & Co-packer foundation tables:
    - brands
    - products
    - skus
    - copackers
    - copacker_contracts
    - brand_performance
    - brand_documents (RAG-ready)
    """
    
    # Brands table
    op.create_table(
        "brands",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("company_name", sa.String(255), nullable=True),
        sa.Column("website", sa.String(500), nullable=True),
        sa.Column("contact_email", sa.String(255), nullable=True),
        sa.Column("contact_phone", sa.String(50), nullable=True),
        sa.Column("target_market", sa.String(255), nullable=True),
        sa.Column("channels", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.text("now()"), nullable=True),
    )
    op.create_index("ix_brands_tenant_id", "brands", ["tenant_id"])
    op.create_index("ix_brands_code", "brands", ["code"])
    
    # Products table
    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("brand_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("image_url", sa.String(500), nullable=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("subcategory", sa.String(100), nullable=True),
        sa.Column("attributes", postgresql.JSONB, nullable=True),
        sa.Column("allergens", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="development"),
        sa.Column("launch_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("discontinuation_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_products_tenant_id", "products", ["tenant_id"])
    op.create_index("ix_products_brand_id", "products", ["brand_id"])
    op.create_index("ix_products_code", "products", ["code"])
    
    # SKUs table
    op.create_table(
        "skus",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sku_code", sa.String(100), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("variant_attributes", postgresql.JSONB, nullable=True),
        sa.Column("package_size", sa.Float(), nullable=True),
        sa.Column("package_unit", sa.String(50), nullable=True),
        sa.Column("units_per_case", sa.Integer(), nullable=True),
        sa.Column("suggested_retail_price", sa.Float(), nullable=True),
        sa.Column("wholesale_price", sa.Float(), nullable=True),
        sa.Column("cost_per_unit", sa.Float(), nullable=True),
        sa.Column("upc", sa.String(50), nullable=True),
        sa.Column("gtin", sa.String(50), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_skus_tenant_id", "skus", ["tenant_id"])
    op.create_index("ix_skus_product_id", "skus", ["product_id"])
    op.create_index("ix_skus_sku_code", "skus", ["sku_code"])
    op.create_index("ix_skus_upc", "skus", ["upc"])
    
    # Copackers table
    op.create_table(
        "copackers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("contact_person", sa.String(255), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("website", sa.String(500), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("state", sa.String(100), nullable=True),
        sa.Column("country", sa.String(100), nullable=True),
        sa.Column("postal_code", sa.String(20), nullable=True),
        sa.Column("capabilities", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("certifications", postgresql.JSONB, nullable=True),
        sa.Column("performance_score", sa.Float(), nullable=True),
        sa.Column("on_time_delivery_rate", sa.Float(), nullable=True),
        sa.Column("quality_rating", sa.Float(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.text("now()"), nullable=True),
    )
    op.create_index("ix_copackers_tenant_id", "copackers", ["tenant_id"])
    op.create_index("ix_copackers_code", "copackers", ["code"])
    
    # Brand Documents table (RAG-ready) - create before copacker_contracts
    op.create_table(
        "brand_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("document_type", sa.String(100), nullable=False),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("brand_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("copacker_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("version", sa.String(50), nullable=False, server_default="1.0"),
        sa.Column("is_latest_version", sa.Boolean(), default=True, nullable=False),
        sa.Column("parent_document_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_indexed", sa.Boolean(), default=False, nullable=False),
        sa.Column("indexed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("uploaded_by", sa.String(255), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("approved_by", sa.String(255), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expiry_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["copacker_id"], ["copackers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_document_id"], ["brand_documents.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_brand_documents_tenant_id", "brand_documents", ["tenant_id"])
    op.create_index("ix_brand_documents_type", "brand_documents", ["document_type"])
    op.create_index("ix_brand_documents_category", "brand_documents", ["category"])
    op.create_index("ix_brand_documents_brand_id", "brand_documents", ["brand_id"])
    op.create_index("ix_brand_documents_is_indexed", "brand_documents", ["is_indexed"])
    op.create_index("ix_brand_documents_content_hash", "brand_documents", ["content_hash"])
    
    # Copacker Contracts table
    op.create_table(
        "copacker_contracts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("brand_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("copacker_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_ids", postgresql.JSONB, nullable=True),
        sa.Column("contract_number", sa.String(100), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("renewal_terms", sa.Text(), nullable=True),
        sa.Column("pricing_model", sa.String(100), nullable=True),
        sa.Column("pricing_details", postgresql.JSONB, nullable=True),
        sa.Column("slas", postgresql.JSONB, nullable=True),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["copacker_id"], ["copackers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["document_id"], ["brand_documents.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_copacker_contracts_tenant_id", "copacker_contracts", ["tenant_id"])
    op.create_index("ix_copacker_contracts_brand_id", "copacker_contracts", ["brand_id"])
    op.create_index("ix_copacker_contracts_copacker_id", "copacker_contracts", ["copacker_id"])
    op.create_index("ix_copacker_contracts_number", "copacker_contracts", ["contract_number"])
    
    # Brand Performance table
    op.create_table(
        "brand_performance",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("brand_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("sku_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_type", sa.String(50), nullable=False),
        sa.Column("units_sold", sa.Integer(), nullable=True),
        sa.Column("gross_revenue", sa.Float(), nullable=True),
        sa.Column("net_revenue", sa.Float(), nullable=True),
        sa.Column("cost_of_goods_sold", sa.Float(), nullable=True),
        sa.Column("gross_margin", sa.Float(), nullable=True),
        sa.Column("gross_margin_pct", sa.Float(), nullable=True),
        sa.Column("additional_metrics", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sku_id"], ["skus.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_brand_performance_tenant_id", "brand_performance", ["tenant_id"])
    op.create_index("ix_brand_performance_brand_id", "brand_performance", ["brand_id"])
    op.create_index("ix_brand_performance_product_id", "brand_performance", ["product_id"])
    op.create_index("ix_brand_performance_sku_id", "brand_performance", ["sku_id"])


def downgrade() -> None:
    """Drop all Brand tables."""
    op.drop_table("brand_performance")
    op.drop_table("copacker_contracts")
    op.drop_table("brand_documents")
    op.drop_table("copackers")
    op.drop_table("skus")
    op.drop_table("products")
    op.drop_table("brands")

