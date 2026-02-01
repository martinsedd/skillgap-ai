"""initial_schema

Revision ID: ef29ff77ef31
Revises:
Create Date: 2026-01-31 19:04:12.470853

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create resumes table
    op.create_table(
        "resumes",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("file_path", sa.String(), nullable=False),
        sa.Column("extracted_text", sa.Text(), nullable=False),
        sa.Column("pinecone_id", sa.String(), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create jobs table
    op.create_table(
        "jobs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("external_id", sa.String(), nullable=False),
        sa.Column("source", sa.Enum("adzuna", "remoteok", name="jobsource"), nullable=False),
        sa.Column("dedup_hash", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("company", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("salary", sa.String(), nullable=True),
        sa.Column("posted_at", sa.DateTime(), nullable=True),
        sa.Column("fetched_at", sa.DateTime(), nullable=False),
        sa.Column("pinecone_id", sa.String(), nullable=False),
        sa.Column("extracted_skills", JSONB, nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("dedup_hash"),
    )
    op.create_index("ix_jobs_dedup_hash", "jobs", ["dedup_hash"])

    # Create interview_sessions table
    op.create_table(
        "interview_sessions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("job_id", sa.String(), nullable=False),
        sa.Column(
            "state",
            sa.Enum("draft", "in_progress", "completed", "abandoned", name="interviewstate"),
            nullable=False,
        ),
        sa.Column("conversation_history", JSONB, nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=True),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["jobs.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Seed default user
    op.execute("INSERT INTO users (id, created_at) VALUES ('default-user', NOW())")


def downgrade() -> None:
    op.drop_table("interview_sessions")
    op.drop_table("jobs")
    op.drop_table("resumes")
    op.drop_table("users")
    op.execute("DROP TYPE interviewstate")
    op.execute("DROP TYPE jobsource")
