"""add parse tracking to source document

Revision ID: 1e56c5812894
Revises: d1becb0e1aaf
Create Date: 2026-04-10 08:51:11.140979
"""
from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision = '1e56c5812894'
down_revision = 'd1becb0e1aaf'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('source_documents', sa.Column('parse_status', sa.String(length=50), nullable=True))
    op.add_column('source_documents', sa.Column('parse_error', sa.Text(), nullable=True))
    op.add_column('source_documents', sa.Column('parsed_at', sa.Date(), nullable=True))
    # Initialize existing records
    op.execute("UPDATE source_documents SET parse_status = 'PENDING' WHERE parse_status IS NULL")


def downgrade() -> None:
    op.drop_column('source_documents', 'parsed_at')
    op.drop_column('source_documents', 'parse_error')
    op.drop_column('source_documents', 'parse_status')
