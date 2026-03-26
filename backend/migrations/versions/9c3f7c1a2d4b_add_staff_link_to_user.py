"""Add staff link to user

Revision ID: 9c3f7c1a2d4b
Revises: bbad2008b8e1
Create Date: 2026-03-26 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9c3f7c1a2d4b'
down_revision = 'bbad2008b8e1'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('user', sa.Column('staff_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_user_staff_id', 'user', 'staff', ['staff_id'], ['id'])


def downgrade():
    op.drop_constraint('fk_user_staff_id', 'user', type_='foreignkey')
    op.drop_column('user', 'staff_id')
