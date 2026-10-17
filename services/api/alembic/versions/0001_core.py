"""Baseline: exact supplied EduRadar v1.0 DDL, sections 4.2-4.5."""

from pathlib import Path

from alembic import op

revision = "0001_core"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    sql = Path(__file__).with_suffix(".sql").read_text(encoding="utf-8")
    op.get_bind().exec_driver_sql(sql)


def downgrade() -> None:
    raise RuntimeError(
        "Destructive downgrade is disabled. Use an approved forward migration or restore plan."
    )
