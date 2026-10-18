import sqlalchemy as sa
from alembic import command

from services.api.db.session import alembic_config
from services.data.normalization.store import digest
from tests.fixtures import make_scope


def test_upgrade_0002_to_publication_guards_preserves_legacy_rows(database_factory):
    engine = database_factory("publication_upgrade")
    with engine.begin() as c:
        cfg = alembic_config()
        cfg.attributes["connection"] = c
        command.upgrade(cfg, "0002_crawler")
        make_scope(c)
        before = digest(
            [dict(r) for r in c.execute(sa.text("SELECT * FROM cutoff_scores")).mappings()]
        )
        command.upgrade(cfg, "head")
        command.upgrade(cfg, "head")
        assert c.scalar(sa.text("SELECT version_num FROM alembic_version")) == "0003_publication"
        assert (
            digest([dict(r) for r in c.execute(sa.text("SELECT * FROM cutoff_scores")).mappings()])
            == before
        )
    engine.dispose()
