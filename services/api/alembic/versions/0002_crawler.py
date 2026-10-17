"""Durable raw crawler runs, shared host policy and attachment schedules."""

from pathlib import Path

from alembic import op

revision = "0002_crawler"
down_revision = "0001_core"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.get_bind().exec_driver_sql(Path(__file__).with_suffix(".sql").read_text(encoding="utf-8"))


def downgrade() -> None:
    raise RuntimeError("Destructive downgrade disabled; use a reviewed forward migration")
