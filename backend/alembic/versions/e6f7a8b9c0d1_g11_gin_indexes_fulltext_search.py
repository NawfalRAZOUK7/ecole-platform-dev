"""G11 — GIN indexes for full-text search (Phase 3D).

Revision ID: e6f7a8b9c0d1
Revises: d5e6f7a8b9c0
Create Date: 2026-03-20

Adds GIN indexes on tsvector columns for full-text search on:
- courses (title, description)
- assignments (title, description)
- content_items (title)
- notifications (title, body)
- activities (title, pedagogical_objective)
- assessments (title)
- parent_feed_items (title, body)

Uses 'simple' text search config for multilingual support (French/Arabic/English).
"""

from alembic import op

revision = "e6f7a8b9c0d1"
down_revision = "d5e6f7a8b9c0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Courses — search on title + description
    op.execute("""
        CREATE INDEX idx_courses_search
        ON courses
        USING GIN (to_tsvector('simple', coalesce(title, '') || ' ' || coalesce(description, '')))
    """)

    # Assignments — search on title + description
    op.execute("""
        CREATE INDEX idx_assignments_search
        ON assignments
        USING GIN (to_tsvector('simple', coalesce(title, '') || ' ' || coalesce(description, '')))
    """)

    # Content items — search on title
    op.execute("""
        CREATE INDEX idx_content_items_search
        ON content_items
        USING GIN (to_tsvector('simple', coalesce(title, '')))
    """)

    # Notifications — search on title + body
    op.execute("""
        CREATE INDEX idx_notifications_search
        ON notifications
        USING GIN (to_tsvector('simple', coalesce(title, '') || ' ' || coalesce(body, '')))
    """)

    # Activities — search on title + pedagogical_objective
    op.execute("""
        CREATE INDEX idx_activities_search
        ON activities
        USING GIN (to_tsvector('simple', coalesce(title, '') || ' ' || coalesce(pedagogical_objective, '')))
    """)

    # Assessments — search on title
    op.execute("""
        CREATE INDEX idx_assessments_search
        ON assessments
        USING GIN (to_tsvector('simple', coalesce(title, '')))
    """)

    # Parent feed items — search on title + body
    op.execute("""
        CREATE INDEX idx_parent_feed_items_search
        ON parent_feed_items
        USING GIN (to_tsvector('simple', coalesce(title, '') || ' ' || coalesce(body, '')))
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_courses_search")
    op.execute("DROP INDEX IF EXISTS idx_assignments_search")
    op.execute("DROP INDEX IF EXISTS idx_content_items_search")
    op.execute("DROP INDEX IF EXISTS idx_notifications_search")
    op.execute("DROP INDEX IF EXISTS idx_activities_search")
    op.execute("DROP INDEX IF EXISTS idx_assessments_search")
    op.execute("DROP INDEX IF EXISTS idx_parent_feed_items_search")
