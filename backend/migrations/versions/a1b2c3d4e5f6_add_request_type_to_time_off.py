"""Add request_type to time_off_request

Revision ID: a1b2c3d4e5f6
Revises: 9c3f7c1a2d4b
Create Date: 2026-03-26 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '9c3f7c1a2d4b'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('time_off_request', sa.Column('request_type', sa.String(20), nullable=False, server_default='pto'))


def downgrade():
    op.drop_column('time_off_request', 'request_type')
