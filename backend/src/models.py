from sqlalchemy import Column, Integer, String, JSON, DateTime, Text, Date
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from .database import Base


class BidProject(Base):
    __tablename__ = "bid_projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    status = Column(String, default="planning")  # planning, executing, reviewing, done

    # Store structured data as JSON for flexibility in V1
    parsed_documents = Column(JSON, default=list)
    requirements = Column(JSON, default=list)
    scoring_items = Column(JSON, default=list)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class EvidenceItem(Base):
    """
    Stores a single piece of evidence material from the company's vault.
    Each record represents one retrievable chunk: a certificate, a contract page,
    a tech screenshot, a bid section paragraph, etc.
    """
    __tablename__ = "evidence_items"

    id = Column(Integer, primary_key=True, index=True)

    # Classification
    category = Column(String, index=True)   # company_credential, project_case, vendor_material, personnel, bid_section
    sub_type = Column(String, index=True)   # license, iso_cert, contract, tech_screenshot, deviation_table, tech_scheme, etc.

    # Content
    title = Column(String)                  # e.g. "ISO9001质量管理体系认证证书"
    text_content = Column(Text)             # full text content of this chunk
    summary = Column(String)                # one-line summary

    # File references
    file_path = Column(String)              # MinIO path or local path to attached file (image/pdf)
    image_paths = Column(JSON, default=list) # list of image paths referenced in this chunk
    source_doc = Column(String)             # source document name, e.g. "商务技术文件.docx"
    source_page = Column(String)            # page range in source, e.g. "P190-P196"
    source_section = Column(String)         # section heading path, e.g. "8.2.1 ISO9001"

    # Vector embedding for semantic search
    embedding = Column(Vector(1024))        # BGE-M3 embedding dimension (1024)

    # Metadata
    tags = Column(JSONB, default=list)      # searchable tags like ["ISO9001", "质量管理"]
    valid_from = Column(Date, nullable=True)
    valid_to = Column(Date, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
