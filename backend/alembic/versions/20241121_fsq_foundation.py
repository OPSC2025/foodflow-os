"""FSQ foundation tables

Revision ID: 20241121_fsq_foundation
Revises: 20241121_plantops_expansion
Create Date: 2024-11-21
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20241121_fsq_foundation"
down_revision: Union[str, None] = "20241121_plantops_expansion"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create FSQ (Food Safety & Quality) foundation tables:
    - suppliers
    - ingredients
    - lots (with parent-child traceability)
    - deviations
    - capas (Corrective and Preventive Actions)
    - haccp_plans
    - ccp_logs
    - documents (RAG-ready)
    """
    
    # Suppliers table
    op.create_table(
        "suppliers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("contact_person", sa.String(255), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("country", sa.String(100), nullable=True),
        sa.Column("certifications", postgresql.JSONB, nullable=True),
        sa.Column("is_approved", sa.Boolean(), default=False, nullable=False),
        sa.Column("approved_by", sa.String(255), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("risk_score", sa.Float(), nullable=True),
        sa.Column("last_audit_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_audit_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.text("now()"), nullable=True),
    )
    op.create_index("ix_suppliers_tenant_id", "suppliers", ["tenant_id"])
    op.create_index("ix_suppliers_code", "suppliers", ["code"])
    op.create_index("ix_suppliers_is_approved", "suppliers", ["is_approved"])
    
    # Ingredients table
    op.create_table(
        "ingredients",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("supplier_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("specification", postgresql.JSONB, nullable=True),
        sa.Column("allergens", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("storage_conditions", sa.Text(), nullable=True),
        sa.Column("shelf_life_days", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_ingredients_tenant_id", "ingredients", ["tenant_id"])
    op.create_index("ix_ingredients_code", "ingredients", ["code"])
    op.create_index("ix_ingredients_supplier_id", "ingredients", ["supplier_id"])
    
    # Lots table (with parent-child traceability)
    op.create_table(
        "lots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("lot_number", sa.String(100), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ingredient_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(50), nullable=False),
        sa.Column("received_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("manufactured_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expiry_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("supplier_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(50), default="active", nullable=False),
        sa.Column("is_on_hold", sa.Boolean(), default=False, nullable=False),
        sa.Column("hold_reason", sa.Text(), nullable=True),
        sa.Column("qc_status", sa.String(50), nullable=True),
        sa.Column("qc_results", postgresql.JSONB, nullable=True),
        sa.Column("storage_location", sa.String(255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["ingredient_id"], ["ingredients.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_lots_tenant_id", "lots", ["tenant_id"])
    op.create_index("ix_lots_lot_number", "lots", ["lot_number"])
    op.create_index("ix_lots_status", "lots", ["status"])
    op.create_index("ix_lots_supplier_id", "lots", ["supplier_id"])
    
    # Lot traceability links (parent-child relationships)
    op.create_table(
        "lot_traceability",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("parent_lot_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("child_lot_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quantity_used", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["parent_lot_id"], ["lots.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["child_lot_id"], ["lots.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_lot_traceability_parent", "lot_traceability", ["parent_lot_id"])
    op.create_index("ix_lot_traceability_child", "lot_traceability", ["child_lot_id"])
    
    # Deviations table
    op.create_table(
        "deviations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("deviation_number", sa.String(100), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(50), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("detected_by", sa.String(255), nullable=True),
        sa.Column("lot_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("line_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(50), default="open", nullable=False),
        sa.Column("investigation_notes", sa.Text(), nullable=True),
        sa.Column("root_cause", sa.Text(), nullable=True),
        sa.Column("immediate_action", sa.Text(), nullable=True),
        sa.Column("closure_notes", sa.Text(), nullable=True),
        sa.Column("closed_by", sa.String(255), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("capa_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["lot_id"], ["lots.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_deviations_tenant_id", "deviations", ["tenant_id"])
    op.create_index("ix_deviations_number", "deviations", ["deviation_number"])
    op.create_index("ix_deviations_status", "deviations", ["status"])
    op.create_index("ix_deviations_severity", "deviations", ["severity"])
    
    # CAPAs table (Corrective and Preventive Actions)
    op.create_table(
        "capas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("capa_number", sa.String(100), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("root_cause", sa.Text(), nullable=False),
        sa.Column("corrective_actions", postgresql.JSONB, nullable=True),
        sa.Column("preventive_actions", postgresql.JSONB, nullable=True),
        sa.Column("status", sa.String(50), default="open", nullable=False),
        sa.Column("priority", sa.String(50), nullable=False),
        sa.Column("owner", sa.String(255), nullable=False),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verification_method", sa.Text(), nullable=True),
        sa.Column("verification_notes", sa.Text(), nullable=True),
        sa.Column("verified_by", sa.String(255), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_effective", sa.Boolean(), nullable=True),
        sa.Column("effectiveness_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.text("now()"), nullable=True),
    )
    op.create_index("ix_capas_tenant_id", "capas", ["tenant_id"])
    op.create_index("ix_capas_number", "capas", ["capa_number"])
    op.create_index("ix_capas_status", "capas", ["status"])
    op.create_index("ix_capas_owner", "capas", ["owner"])
    
    # Add foreign key from deviations to capas
    op.create_foreign_key(
        "fk_deviations_capa",
        "deviations",
        "capas",
        ["capa_id"],
        ["id"],
        ondelete="SET NULL",
    )
    
    # HACCP Plans table
    op.create_table(
        "haccp_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plan_name", sa.String(255), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("version", sa.String(50), nullable=False),
        sa.Column("effective_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("review_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ccps", postgresql.JSONB, nullable=True),
        sa.Column("hazards", postgresql.JSONB, nullable=True),
        sa.Column("control_measures", postgresql.JSONB, nullable=True),
        sa.Column("approved_by", sa.String(255), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.text("now()"), nullable=True),
    )
    op.create_index("ix_haccp_plans_tenant_id", "haccp_plans", ["tenant_id"])
    op.create_index("ix_haccp_plans_product_id", "haccp_plans", ["product_id"])
    
    # CCP Logs table (Critical Control Point monitoring)
    op.create_table(
        "ccp_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("haccp_plan_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ccp_name", sa.String(255), nullable=False),
        sa.Column("monitored_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("monitored_by", sa.String(255), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(50), nullable=False),
        sa.Column("critical_limit_min", sa.Float(), nullable=True),
        sa.Column("critical_limit_max", sa.Float(), nullable=True),
        sa.Column("is_in_spec", sa.Boolean(), nullable=False),
        sa.Column("corrective_action", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["haccp_plan_id"], ["haccp_plans.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_ccp_logs_tenant_id", "ccp_logs", ["tenant_id"])
    op.create_index("ix_ccp_logs_plan_id", "ccp_logs", ["haccp_plan_id"])
    op.create_index("ix_ccp_logs_monitored_at", "ccp_logs", ["monitored_at"])
    op.create_index("ix_ccp_logs_is_in_spec", "ccp_logs", ["is_in_spec"])
    
    # Documents table (RAG-ready for vector embeddings)
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("document_type", sa.String(100), nullable=False),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=True),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("version", sa.String(50), nullable=False),
        sa.Column("is_latest_version", sa.Boolean(), default=True, nullable=False),
        sa.Column("parent_document_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("uploaded_by", sa.String(255), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("approved_by", sa.String(255), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expiry_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("is_indexed", sa.Boolean(), default=False, nullable=False),
        sa.Column("indexed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["parent_document_id"], ["documents.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_documents_tenant_id", "documents", ["tenant_id"])
    op.create_index("ix_documents_type", "documents", ["document_type"])
    op.create_index("ix_documents_category", "documents", ["category"])
    op.create_index("ix_documents_is_indexed", "documents", ["is_indexed"])
    op.create_index("ix_documents_content_hash", "documents", ["content_hash"])


def downgrade() -> None:
    """Drop all FSQ tables."""
    op.drop_table("documents")
    op.drop_table("ccp_logs")
    op.drop_table("haccp_plans")
    op.drop_table("capas")
    op.drop_table("deviations")
    op.drop_table("lot_traceability")
    op.drop_table("lots")
    op.drop_table("ingredients")
    op.drop_table("suppliers")

