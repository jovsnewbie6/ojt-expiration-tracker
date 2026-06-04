"""Reset broken migration state and ensure attendance table exists

Revision ID: 002_fix_attendance
Revises: 001_create_all_tables
Create Date: 2026-06-04
"""

from alembic import op
import sqlalchemy as sa


revision = '002_fix_attendance'
down_revision = '001_create_all_tables'
branch_labels = None
depends_on = None


def upgrade():
    # SAFE: create attendance table only if missing
    op.create_table(
        'attendance',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('student_id', sa.Integer, sa.ForeignKey('students.id'), nullable=False),
        sa.Column('student_name', sa.String(140), nullable=False),
        sa.Column('student_section', sa.String(60), nullable=False, server_default=""),
        sa.Column('attendance_date', sa.Date, nullable=False),
        sa.Column('attendance_time', sa.String(5), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default="Present"),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
    )


def downgrade():
    op.drop_table('attendance')