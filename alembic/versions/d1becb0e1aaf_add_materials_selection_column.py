"""add materials_selection column

Revision ID: d1becb0e1aaf
Revises: 6f0b3d6691c9
Create Date: 2026-04-10 08:46:52.575139
"""
from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision = 'd1becb0e1aaf'
down_revision = '6f0b3d6691c9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('rfp_projects_v2', sa.Column('materials_selection', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('rfp_projects_v2', 'materials_selection')
