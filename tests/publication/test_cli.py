import json
import os
import subprocess
import sys
from pathlib import Path

from tests.publication.helpers import fact_command
from tests.publication.test_publish import prepared as prepared


def test_cli_inspect_plan_apply_and_replay_are_real_local_commands(prepared, tmp_path):
    admin, e, p, boot = prepared
    command = fact_command(p, boot["ids"])
    file = tmp_path / "TEST-ONLY-review.json"
    file.write_text(command.model_dump_json(), encoding="utf-8")
    env = os.environ.copy() | {
        "POSTGRES_DB": e.url.database,
        "PUBLICATION_DB_USER": e.url.username,
        "PUBLICATION_DB_PASSWORD": e.url.password,
    }

    def cli(*args, success=True):
        result = subprocess.run(
            [sys.executable, "-m", "services.data.publication", *args],
            env=env,
            capture_output=True,
            encoding="utf-8",
            timeout=40,
        )
        assert (result.returncode == 0) == success, result.stderr
        return json.loads(result.stdout if success else result.stderr)

    assert cli("list")
    packet = cli("inspect", "--resolution", p["resolution_id"], "--candidate", p["candidate_key"])
    assert packet["packet_sha256"] == p["packet_sha256"]
    preview = cli("plan", "--resolution", p["resolution_id"], "--candidate", p["candidate_key"])
    assert not preview["can_publish"] and "scale" in preview["needs_decision"]
    assert cli("plan", "--file", str(file))["can_apply"]
    decision = cli("apply", "--file", str(file))
    result = cli("apply", "--decision", decision["decision_id"])
    assert result["status"] == "published"
    assert cli("replay", "--decision", decision["decision_id"])["cached"]
    error = cli(
        "inspect",
        "--resolution",
        p["resolution_id"],
        "--candidate",
        p["candidate_key"],
        "--output",
        "private-review.json",
        success=False,
    )
    assert error["blocked"] and not Path("private-review.json").exists()
