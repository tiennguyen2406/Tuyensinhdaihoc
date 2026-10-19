"""Explicit operator command, using migration-owner credentials from the environment.
Creates NOLOGIN group roles and grants only; never creates logins/passwords or edits .env.
"""

from services.api.db.session import engine, schema_is_current
from services.data.publication.roles import provision_roles

if __name__ == "__main__":
    with engine.begin() as c:
        if not schema_is_current(c):
            raise RuntimeError("Run reviewed migrations first")
        provision_roles(c)
    print(
        "Publication group-role grants installed. No login memberships or credentials configured."
    )
