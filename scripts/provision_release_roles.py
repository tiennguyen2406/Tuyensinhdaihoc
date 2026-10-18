"""Owner-run T09 group grants + audit. No login/password or .env changes."""

from services.api.db.session import engine, schema_is_current
from services.data.releases.roles import provision_roles

if __name__ == "__main__":
    with engine.begin() as c:
        if not schema_is_current(c):
            raise RuntimeError("Run reviewed migrations first")
        provision_roles(c)
    print("Release capability provisioned and audited; no logins/credentials configured.")
