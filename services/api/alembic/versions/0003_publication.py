"""Add append-only audit and T08-managed history guards, without changing existing data."""

from pathlib import Path

from alembic import op

revision = "0003_publication"
down_revision = "0002_crawler"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.get_bind().exec_driver_sql(Path(__file__).with_suffix(".sql").read_text(encoding="utf-8"))


def downgrade() -> None:
    raise RuntimeError("Destructive downgrade disabled; use reviewed forward migration")
