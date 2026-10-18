"""Add immutable releases and audited refresh transition guards; no data rewrite."""

from pathlib import Path

from alembic import op

revision = "0004_releases"
down_revision = "0003_publication"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.get_bind().exec_driver_sql(Path(__file__).with_suffix(".sql").read_text(encoding="utf-8"))


def downgrade() -> None:
    raise RuntimeError("Destructive downgrade disabled; use reviewed forward migration")
