"""Add reset token fields to user

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-30 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('user', sa.Column('reset_token', sa.String(200), nullable=True))
    op.add_column('user', sa.Column('reset_token_expiry', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('user', 'reset_token_expiry')
    op.drop_column('user', 'reset_token')
