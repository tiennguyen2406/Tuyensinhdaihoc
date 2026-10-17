import json
import socket
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROBE = """
import json
from fastapi.testclient import TestClient
from services.api.main import app

with TestClient(app) as client:
    live = client.get('/health/live')
    ready = client.get('/health/ready')
    repeated = client.get('/health/ready')
    print(json.dumps({
        'live_status': live.status_code,
        'ready_status': ready.status_code,
        'ready_body': ready.json(),
        'repeated_status': repeated.status_code,
    }))
"""


def probe(environment):
    result = subprocess.run(
        [sys.executable, "-c", PROBE],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=20,
        check=True,
    )
    return json.loads(result.stdout)


def test_ready_checks_real_postgres(test_environment):
    result = probe(test_environment)
    assert result["live_status"] == 200
    assert result["ready_status"] == 200
    assert result["ready_body"] == {"status": "ok", "database": "connected"}
    assert result["repeated_status"] == 200


def test_unreachable_database_returns_503_while_live_stays_200(test_environment):
    with socket.socket() as reserved:
        reserved.bind(("127.0.0.1", 0))
        environment = test_environment.copy()
        environment["POSTGRES_HOST"] = "127.0.0.1"
        environment["POSTGRES_PORT"] = str(reserved.getsockname()[1])
        result = probe(environment)
    assert result["live_status"] == 200
    assert result["ready_status"] == 503
    assert result["ready_body"] == {"status": "unavailable", "database": "unavailable"}
    assert result["repeated_status"] == 503
