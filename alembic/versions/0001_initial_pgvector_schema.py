"""initial pgvector schema

Revision ID: 0001_initial_pgvector
Revises: None
Create Date: 2026-04-08 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


revision = "0001_initial_pgvector"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "companies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("unified_social_credit_code", sa.String(length=100), nullable=True),
        sa.Column("registered_capital", sa.String(length=100), nullable=True),
        sa.Column("address", sa.String(length=500), nullable=True),
        sa.Column("legal_representative", sa.String(length=100), nullable=True),
    )
    op.create_index("ix_companies_id", "companies", ["id"])
    op.create_index("ix_companies_company_name", "companies", ["company_name"], unique=True)
    op.create_index("ix_companies_unified_social_credit_code", "companies", ["unified_social_credit_code"], unique=True)

    op.create_table(
        "source_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("file_type", sa.String(length=50), nullable=False),
        sa.Column("local_path", sa.String(length=500), nullable=False),
        sa.Column("upload_date", sa.Date(), nullable=True),
    )
    op.create_index("ix_source_documents_id", "source_documents", ["id"])

    op.create_table(
        "enterprise_certificates_v2",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("source_doc_id", sa.Integer(), sa.ForeignKey("source_documents.id"), nullable=True),
        sa.Column("cert_type", sa.String(length=100), nullable=True),
        sa.Column("cert_level", sa.String(length=50), nullable=True),
        sa.Column("raw_name", sa.String(length=255), nullable=False),
        sa.Column("certification_scope", sa.Text(), nullable=True),
        sa.Column("issue_date", sa.Date(), nullable=True),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column("embedding", Vector(1536), nullable=True),
    )
    op.create_index("ix_enterprise_certificates_v2_id", "enterprise_certificates_v2", ["id"])
    op.create_index("ix_enterprise_certificates_v2_cert_type", "enterprise_certificates_v2", ["cert_type"])

    op.create_table(
        "enterprise_cases_v2",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("source_doc_id", sa.Integer(), sa.ForeignKey("source_documents.id"), nullable=True),
        sa.Column("project_name", sa.String(length=255), nullable=False),
        sa.Column("industry", sa.String(length=100), nullable=True),
        sa.Column("contract_amount", sa.Float(), nullable=True),
        sa.Column("sign_date", sa.Date(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("compliance_keywords", sa.Text(), nullable=True),
        sa.Column("image_gallery", sa.Text(), nullable=True),
        sa.Column("embedding", Vector(1536), nullable=True),
    )
    op.create_index("ix_enterprise_cases_v2_id", "enterprise_cases_v2", ["id"])
    op.create_index("ix_enterprise_cases_v2_industry", "enterprise_cases_v2", ["industry"])
    op.create_index("ix_enterprise_cases_v2_contract_amount", "enterprise_cases_v2", ["contract_amount"])

    op.create_table(
        "enterprise_personnel",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("role", sa.String(length=100), nullable=True),
        sa.Column("level", sa.String(length=50), nullable=True),
        sa.Column("years_of_experience", sa.Integer(), nullable=True),
        sa.Column("resume_text", sa.Text(), nullable=True),
        sa.Column("social_security_image_url", sa.String(length=500), nullable=True),
        sa.Column("embedding", Vector(1536), nullable=True),
    )
    op.create_index("ix_enterprise_personnel_id", "enterprise_personnel", ["id"])

    op.create_table(
        "company_assets",
        sa.Column("id", sa.String(length=50), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("asset_name", sa.String(length=255), nullable=False),
        sa.Column("asset_type", sa.String(length=50), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("asset_tag", sa.String(length=100), nullable=True),
        sa.Column("local_path", sa.String(length=500), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("upload_date", sa.Date(), nullable=True),
    )
    op.create_index("ix_company_assets_asset_tag", "company_assets", ["asset_tag"])

    op.create_table(
        "asset_chunks_v2",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("source_doc_id", sa.Integer(), sa.ForeignKey("source_documents.id"), nullable=False),
        sa.Column("chunk_type", sa.String(length=50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(1536), nullable=True),
    )
    op.create_index("ix_asset_chunks_v2_id", "asset_chunks_v2", ["id"])
    op.create_index("ix_asset_chunks_v2_company_id", "asset_chunks_v2", ["company_id"])
    op.create_index("ix_asset_chunks_v2_source_doc_id", "asset_chunks_v2", ["source_doc_id"])

    op.create_table(
        "rfp_projects_v2",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("project_name", sa.String(length=255), nullable=False),
        sa.Column("rfp_source_id", sa.Integer(), sa.ForeignKey("source_documents.id"), nullable=True),
        sa.Column("budget", sa.Float(), nullable=True),
        sa.Column("deadline", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="ANALYZING"),
    )
    op.create_index("ix_rfp_projects_v2_id", "rfp_projects_v2", ["id"])
    op.create_index("ix_rfp_projects_v2_project_name", "rfp_projects_v2", ["project_name"])

    op.create_table(
        "rfp_requirements_v2",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("rfp_projects_v2.id"), nullable=False),
        sa.Column("original_section", sa.String(length=255), nullable=True),
        sa.Column("clause_index", sa.String(length=50), nullable=True),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("is_fatal", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("max_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("evidence_required", sa.Text(), nullable=True),
        sa.Column("match_status", sa.String(length=50), nullable=True, server_default="UNKNOWN"),
        sa.Column("match_comment", sa.Text(), nullable=True),
        sa.Column("linked_asset_id", sa.Integer(), nullable=True),
    )
    op.create_index("ix_rfp_requirements_v2_id", "rfp_requirements_v2", ["id"])

    op.create_table(
        "project_materials_v2",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("rfp_projects_v2.id"), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("file_type", sa.String(length=50), nullable=False),
        sa.Column("local_path", sa.String(length=500), nullable=False),
        sa.Column("upload_date", sa.Date(), nullable=True),
        sa.Column("parsed_content", sa.Text(), nullable=True),
    )
    op.create_index("ix_project_materials_v2_id", "project_materials_v2", ["id"])

    op.create_table(
        "bid_drafts_v2",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("rfp_projects_v2.id"), nullable=False),
        sa.Column("section_title", sa.String(length=255), nullable=False),
        sa.Column("section_index", sa.String(length=50), nullable=False),
        sa.Column("content_markdown", sa.Text(), nullable=True),
        sa.Column("generation_status", sa.String(length=50), nullable=False, server_default="PENDING"),
        sa.Column("audit_logs", sa.JSON(), nullable=True),
        sa.Column("source_fragments", sa.JSON(), nullable=True),
        sa.Column("winning_points", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("last_updated", sa.Date(), nullable=True),
    )
    op.create_index("ix_bid_drafts_v2_id", "bid_drafts_v2", ["id"])


def downgrade() -> None:
    op.drop_index("ix_bid_drafts_v2_id", table_name="bid_drafts_v2")
    op.drop_table("bid_drafts_v2")

    op.drop_index("ix_project_materials_v2_id", table_name="project_materials_v2")
    op.drop_table("project_materials_v2")

    op.drop_index("ix_rfp_requirements_v2_id", table_name="rfp_requirements_v2")
    op.drop_table("rfp_requirements_v2")

    op.drop_index("ix_rfp_projects_v2_project_name", table_name="rfp_projects_v2")
    op.drop_index("ix_rfp_projects_v2_id", table_name="rfp_projects_v2")
    op.drop_table("rfp_projects_v2")

    op.drop_index("ix_asset_chunks_v2_source_doc_id", table_name="asset_chunks_v2")
    op.drop_index("ix_asset_chunks_v2_company_id", table_name="asset_chunks_v2")
    op.drop_index("ix_asset_chunks_v2_id", table_name="asset_chunks_v2")
    op.drop_table("asset_chunks_v2")

    op.drop_index("ix_company_assets_asset_tag", table_name="company_assets")
    op.drop_table("company_assets")

    op.drop_index("ix_enterprise_personnel_id", table_name="enterprise_personnel")
    op.drop_table("enterprise_personnel")

    op.drop_index("ix_enterprise_cases_v2_contract_amount", table_name="enterprise_cases_v2")
    op.drop_index("ix_enterprise_cases_v2_industry", table_name="enterprise_cases_v2")
    op.drop_index("ix_enterprise_cases_v2_id", table_name="enterprise_cases_v2")
    op.drop_table("enterprise_cases_v2")

    op.drop_index("ix_enterprise_certificates_v2_cert_type", table_name="enterprise_certificates_v2")
    op.drop_index("ix_enterprise_certificates_v2_id", table_name="enterprise_certificates_v2")
    op.drop_table("enterprise_certificates_v2")

    op.drop_index("ix_source_documents_id", table_name="source_documents")
    op.drop_table("source_documents")

    op.drop_index("ix_companies_unified_social_credit_code", table_name="companies")
    op.drop_index("ix_companies_company_name", table_name="companies")
    op.drop_index("ix_companies_id", table_name="companies")
    op.drop_table("companies")
