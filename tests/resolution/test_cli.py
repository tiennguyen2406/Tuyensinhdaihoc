import json
import subprocess
import sys
from pathlib import Path


def test_offline_cli_preview_run_replay_and_private_output_guard(test_environment, migrated_engine):
    from tests.resolution.test_store import t06

    with migrated_engine.begin() as c:
        job = t06(c)
    env = test_environment | {"PYTHONIOENCODING": "cp1252"}

    def cli(*args):
        p = subprocess.run(
            [sys.executable, "-m", "services.data.resolution", *args],
            env=env,
            capture_output=True,
            encoding="utf-8",
            timeout=40,
        )
        assert p.returncode == 0, p.stderr
        return json.loads(p.stdout)

    preview = cli("preview", "--normalization-job", job)
    assert preview["persisted"] is False and preview["summary"]["candidates"] == 1
    run = cli("run", "--normalization-job", job)
    assert run["inserted"] == 1
    replay = cli("replay", "--job", run["job_id"])
    assert replay["cached"] and replay["inserted"] == 0
    assert cli("affected", "--entry", "not-an-entry") == []
    denied = subprocess.run(
        [
            sys.executable,
            "-m",
            "services.data.resolution",
            "preview",
            "--normalization-job",
            job,
            "--output",
            "entity-private.json",
        ],
        env=env,
        capture_output=True,
        timeout=40,
    )
    assert denied.returncode != 0 and not Path("entity-private.json").exists()


def test_gold_evaluator_keeps_partitions_and_no_fuzzy_auto_claim():
    from services.data.resolution.evaluate import evaluate

    result = evaluate(Path("tests/resolution/gold.json"))
    assert result["total_cases"] == 280
    assert result["splits"]["calibration"]["cases"] == 80
    assert result["splits"]["evaluation"]["cases"] == 200
    assert result["splits"]["evaluation"]["correct_decisions"] == 200
    assert result["splits"]["evaluation"]["fuzzy_labelled_cases"] == 40
    assert result["splits"]["evaluation"]["fuzzy_auto_links"] == 0
    assert result["splits"]["evaluation"]["precision_wilson_95"][0] < 0.995
