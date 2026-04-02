"""add multi-tenancy (clinic model)

Revision ID: c1d2e3f4a5b6
Revises: b2c3d4e5f6a7
Create Date: 2026-04-02

"""
from alembic import op
import sqlalchemy as sa

revision = 'c1d2e3f4a5b6'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Create clinic table
    op.create_table('clinic',
        sa.Column('id',          sa.Integer(),    nullable=False),
        sa.Column('name',        sa.String(120),  nullable=False),
        sa.Column('invite_code', sa.String(60),   nullable=False),
        sa.Column('created_at',  sa.DateTime(),   nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('invite_code'),
    )

    # 2. Add clinic_id to staff
    op.add_column('staff', sa.Column('clinic_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_staff_clinic_id', 'staff', 'clinic', ['clinic_id'], ['id'])
    op.create_index('ix_staff_clinic_id', 'staff', ['clinic_id'])

    # 3. Fix staff_area: drop global unique on name, add clinic_id, add composite unique
    op.drop_constraint('staff_area_name_key', 'staff_area', type_='unique')
    op.add_column('staff_area', sa.Column('clinic_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_staffarea_clinic_id', 'staff_area', 'clinic', ['clinic_id'], ['id'])
    op.create_index('ix_staffarea_clinic_id', 'staff_area', ['clinic_id'])
    op.create_unique_constraint('uq_staffarea_clinic_name', 'staff_area', ['clinic_id', 'name'])

    # 4. Add clinic_id to shift
    op.add_column('shift', sa.Column('clinic_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_shift_clinic_id', 'shift', 'clinic', ['clinic_id'], ['id'])
    op.create_index('ix_shift_clinic_date', 'shift', ['clinic_id', 'date'])

    # 5. Add clinic_id to time_off_request
    op.add_column('time_off_request', sa.Column('clinic_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_tor_clinic_id', 'time_off_request', 'clinic', ['clinic_id'], ['id'])
    op.create_index('ix_tor_clinic_id', 'time_off_request', ['clinic_id'])

    # 6. Add clinic_id to ai_suggestion
    op.add_column('ai_suggestion', sa.Column('clinic_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_aisugg_clinic_id', 'ai_suggestion', 'clinic', ['clinic_id'], ['id'])

    # 7. Add clinic_id to user; drop global unique constraints; add composite ones
    op.add_column('user', sa.Column('clinic_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_user_clinic_id', 'user', 'clinic', ['clinic_id'], ['id'])
    op.create_index('ix_user_clinic_id', 'user', ['clinic_id'])
    op.drop_constraint('user_email_key',    'user', type_='unique')
    op.drop_constraint('user_username_key', 'user', type_='unique')
    op.create_unique_constraint('uq_user_clinic_email',    'user', ['clinic_id', 'email'])
    op.create_unique_constraint('uq_user_clinic_username', 'user', ['clinic_id', 'username'])


def downgrade():
    # Reverse user changes
    op.drop_constraint('uq_user_clinic_username', 'user', type_='unique')
    op.drop_constraint('uq_user_clinic_email',    'user', type_='unique')
    op.create_unique_constraint('user_username_key', 'user', ['username'])
    op.create_unique_constraint('user_email_key',    'user', ['email'])
    op.drop_index('ix_user_clinic_id', table_name='user')
    op.drop_constraint('fk_user_clinic_id', 'user', type_='foreignkey')
    op.drop_column('user', 'clinic_id')

    # Reverse ai_suggestion
    op.drop_constraint('fk_aisugg_clinic_id', 'ai_suggestion', type_='foreignkey')
    op.drop_column('ai_suggestion', 'clinic_id')

    # Reverse time_off_request
    op.drop_index('ix_tor_clinic_id', table_name='time_off_request')
    op.drop_constraint('fk_tor_clinic_id', 'time_off_request', type_='foreignkey')
    op.drop_column('time_off_request', 'clinic_id')

    # Reverse shift
    op.drop_index('ix_shift_clinic_date', table_name='shift')
    op.drop_constraint('fk_shift_clinic_id', 'shift', type_='foreignkey')
    op.drop_column('shift', 'clinic_id')

    # Reverse staff_area
    op.drop_constraint('uq_staffarea_clinic_name', 'staff_area', type_='unique')
    op.drop_index('ix_staffarea_clinic_id', table_name='staff_area')
    op.drop_constraint('fk_staffarea_clinic_id', 'staff_area', type_='foreignkey')
    op.drop_column('staff_area', 'clinic_id')
    op.create_unique_constraint('staff_area_name_key', 'staff_area', ['name'])

    # Reverse staff
    op.drop_index('ix_staff_clinic_id', table_name='staff')
    op.drop_constraint('fk_staff_clinic_id', 'staff', type_='foreignkey')
    op.drop_column('staff', 'clinic_id')

    # Drop clinic table
    op.drop_table('clinic')
