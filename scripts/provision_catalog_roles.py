"""Owner-run grants for live catalog reader; no login/password changes."""

from services.api.catalog.roles import provision_reader
from services.api.db.session import engine, schema_is_current

if __name__ == "__main__":
    with engine.begin() as c:
        if not schema_is_current(c):
            raise RuntimeError("Run reviewed migrations first")
        provision_reader(c)
    print("Catalog reader grants provisioned and audited. No logins or credentials created.")
