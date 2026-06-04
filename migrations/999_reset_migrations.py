"""Reset broken migration state safely

Revision ID: 999_reset_migrations
Revises: 001_create_all_tables
"""

from alembic import op
import sqlalchemy as sa

revision = "999_reset_migrations"
down_revision = "001_create_all_tables"
branch_labels = None
depends_on = None


def upgrade():
    # Ensure attendance table exists (safe recreate)
    op.create_table(
        "attendance",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("student_id", sa.Integer, sa.ForeignKey("students.id"), nullable=False),
        sa.Column("student_name", sa.String(140), nullable=False),
        sa.Column("student_section", sa.String(60), nullable=False),
        sa.Column("attendance_date", sa.Date, nullable=False),
        sa.Column("attendance_time", sa.String(5), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("attendance")