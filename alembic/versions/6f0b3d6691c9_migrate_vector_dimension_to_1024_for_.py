"""migrate vector dimension to 1024 for bge-m3

Revision ID: 6f0b3d6691c9
Revises: 0001_initial_pgvector
Create Date: 2026-04-09 14:44:55.988232
"""
from alembic import op
import sqlalchemy as sa



from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = '6f0b3d6691c9'
down_revision = '0001_initial_pgvector'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Clear existing embeddings first as they are incompatible with the new dimension
    op.execute("UPDATE enterprise_certificates_v2 SET embedding = NULL")
    op.execute("UPDATE enterprise_cases_v2 SET embedding = NULL")
    op.execute("UPDATE enterprise_personnel SET embedding = NULL")
    op.execute("UPDATE asset_chunks_v2 SET embedding = NULL")

    # Alter vector columns from 1536 to 1024
    op.alter_column('enterprise_certificates_v2', 'embedding', type_=Vector(1024))
    op.alter_column('enterprise_cases_v2', 'embedding', type_=Vector(1024))
    op.alter_column('enterprise_personnel', 'embedding', type_=Vector(1024))
    op.alter_column('asset_chunks_v2', 'embedding', type_=Vector(1024))

def downgrade() -> None:
    op.alter_column('enterprise_certificates_v2', 'embedding', type_=Vector(1536), postgresql_using='embedding::vector(1536)')
    op.alter_column('enterprise_cases_v2', 'embedding', type_=Vector(1536), postgresql_using='embedding::vector(1536)')
    op.alter_column('enterprise_personnel', 'embedding', type_=Vector(1536), postgresql_using='embedding::vector(1536)')
    op.alter_column('asset_chunks_v2', 'embedding', type_=Vector(1536), postgresql_using='embedding::vector(1536)')
