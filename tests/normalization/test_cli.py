import json
import subprocess
import sys
from pathlib import Path


def test_offline_preview_and_versioned_run_replay(test_environment, migrated_engine):
    import sqlalchemy as sa

    from services.api.db.models import observations
    from tests.normalization.test_store import seed

    with migrated_engine.begin() as c:
        identifier = seed(c)
        snapshot = c.execute(
            sa.select(observations.c.snapshot_id).where(observations.c.id == identifier)
        ).scalar_one()
    env = test_environment | {"PYTHONIOENCODING": "cp1252"}

    def cli(*args):
        p = subprocess.run(
            [sys.executable, "-m", "services.data.normalization", *args],
            env=env,
            capture_output=True,
            encoding="utf-8",
            timeout=30,
        )
        assert p.returncode == 0, p.stderr
        return json.loads(p.stdout)

    preview = cli("preview", "--snapshot", str(snapshot))
    assert preview["persisted"] is False and preview["summary"]["inputs"] == 1
    run = cli("run", "--snapshot", str(snapshot))
    assert run["inserted"] == 1
    replay = cli("replay", "--job", run["job_id"])
    assert replay["inserted"] == 0 and replay["cached"]
    denied = subprocess.run(
        [
            sys.executable,
            "-m",
            "services.data.normalization",
            "preview",
            "--snapshot",
            str(snapshot),
            "--output",
            "normalizer-export.json",
        ],
        env=env,
        capture_output=True,
        timeout=30,
    )
    assert denied.returncode != 0 and not Path("normalizer-export.json").exists()
