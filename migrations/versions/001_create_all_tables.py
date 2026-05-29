"""Create all application tables from scratch

Revision ID: 001_create_all_tables
Revises: 
Create Date: 2026-05-29 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_create_all_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### Create Permission table ###
    op.create_table('permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=60), nullable=False),
        sa.Column('description', sa.String(length=200), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # ### Create Users table ###
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=80), nullable=False),
        sa.Column('password_hash', sa.String(length=256), nullable=False),
        sa.Column('role', sa.String(length=30), nullable=False, server_default='admin'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username')
    )

    # ### Create Students table ###
    op.create_table('students',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=120), nullable=True),
        sa.Column('student_number', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=140), nullable=False),
        sa.Column('year_section', sa.String(length=60), nullable=False),
        sa.Column('password_hash', sa.String(length=256), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('role', sa.String(length=30), nullable=False, server_default='student'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('student_number')
    )

    # ### Create StudentRecord table ###
    op.create_table('student_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=140), nullable=False),
        sa.Column('course', sa.String(length=80), nullable=False),
        sa.Column('year_section', sa.String(length=60), nullable=False, server_default=''),
        sa.Column('college_year', sa.String(length=30), nullable=True, server_default=''),
        sa.Column('section', sa.String(length=50), nullable=True, server_default=''),
        sa.Column('company_name', sa.String(length=120), nullable=False, server_default=''),
        sa.Column('business_nature', sa.String(length=120), nullable=False, server_default=''),
        sa.Column('validity', sa.String(length=60), nullable=False, server_default=''),
        sa.Column('notarized_date', sa.Date(), nullable=True),
        sa.Column('student_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('attachments', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='Pending'),
        sa.Column('has_resume', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('has_med_cert', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('has_consent_form', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('has_moa', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('has_insurance', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('has_intent_letter', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('has_endorsement_letter', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('is_complete', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('expiration_date', sa.Date(), nullable=False),
        sa.Column('comments', sa.Text(), nullable=True, server_default=''),
        sa.Column('progress', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # ### Create user_permissions junction table ###
    op.create_table('user_permissions',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('permission_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('user_id', 'permission_id')
    )

    # ### Create student_permissions junction table ###
    op.create_table('student_permissions',
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('permission_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ),
        sa.PrimaryKeyConstraint('student_id', 'permission_id')
    )


def downgrade():
    # ### Drop all tables in reverse order ###
    op.drop_table('student_permissions')
    op.drop_table('user_permissions')
    op.drop_table('student_records')
    op.drop_table('students')
    op.drop_table('users')
    op.drop_table('permissions')
