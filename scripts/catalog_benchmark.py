"""Retained synthetic PostgreSQL catalog benchmark; no DROP or pilot writes.

Run before in a process that imports the old catalog modules before implementation,
then run after against the same --database. Outputs contain no connection URLs.
"""

import argparse
import contextvars
import hashlib
import json
import os
import platform
import re
import socket
import statistics
import subprocess
import sys
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen

import psutil
import sqlalchemy as sa
from alembic import command
from fastapi.testclient import TestClient

from services.api.catalog import queries
from services.api.catalog.router import catalog_snapshot
from services.api.db.session import alembic_config, engine, schema_is_current
from services.api.main import app
from tests.catalog.scale_fixture import seed_catalog, synthetic_id

OUTPUT = Path("state/catalog/t10-sql-20261019")
CURRENT = contextvars.ContextVar("catalog_benchmark", default=None)


def guarded_name(value):
    if not re.fullmatch(r"tuyensinh_test_[a-z0-9_]+", value):
        raise ValueError("Only named tuyensinh_test_* synthetic databases are accepted")
    return value


def write_result(path, data):
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def prepare(name, facts, phase):
    guarded_name(name)
    db = sa.create_engine(
        engine.url.set(database=name),
        pool_size=20,
        max_overflow=0,
        pool_timeout=30,
        hide_parameters=True,
    )
    if phase in {"before", "seed"}:
        admin = sa.create_engine(
            engine.url.set(database="postgres"), isolation_level="AUTOCOMMIT", hide_parameters=True
        )
        with admin.connect() as c:
            if c.scalar(sa.text("SELECT 1 FROM pg_database WHERE datname=:name"), {"name": name}):
                raise ValueError("Before phase requires a new database; existing DB retained")
            c.exec_driver_sql(f'CREATE DATABASE "{name}"')
        admin.dispose()
        start = time.perf_counter()
        with db.connect() as c:
            config = alembic_config()
            config.attributes["connection"] = c
            command.upgrade(config, "head")
        migration_seconds = time.perf_counter() - start
        start = time.perf_counter()
        with db.begin() as c:
            seeded = seed_catalog(c, facts)
        seed_seconds = time.perf_counter() - start
        with db.begin() as c:
            c.exec_driver_sql("ANALYZE")
        write_result(
            OUTPUT / f"{name}-seed.json",
            dict(
                database=name,
                facts=facts,
                migration_seconds=migration_seconds,
                seed_seconds=seed_seconds,
                rows=seeded,
                synthetic_source_domain="example.invalid",
            ),
        )
        print(f"SEEDED {name}: {facts} facts in {seed_seconds:.3f}s", flush=True)
    else:
        with db.connect() as c:
            count, all_synthetic = c.execute(
                sa.text("""
                SELECT count(*), bool_and(publication_group_key='SYNTHETIC BENCHMARK ONLY')
                FROM cutoff_scores
            """)
            ).one()
            if count != facts or not all_synthetic:
                raise ValueError(
                    "After phase requires the retained synthetic fixture with exact count"
                )
    return db


def install_measurement(db, query_cap):
    def before(c, cursor, statement, parameters, context, many):
        measure = c.info.get("benchmark")
        if measure is None:
            return
        context._benchmark_start = time.perf_counter()
        measure["query_count"] += 1
        if query_cap and measure["query_count"] > query_cap:
            measure["query_cap_exceeded"] = True
            raise RuntimeError("Synthetic baseline request query budget exceeded")
        if statement.lstrip().upper().startswith("SELECT"):
            signature = re.sub(r"\([^)]*\)", "(...)", statement)
            if (
                signature not in measure["seen_sql"]
                and len(measure["sql"]) < 18
                and len(parameters) <= 250
            ):
                measure["seen_sql"].add(signature)
                measure["sql"].append((statement, parameters))

    def after(c, cursor, statement, parameters, context, many):
        measure = c.info.get("benchmark")
        if measure is not None and statement.lstrip().upper().startswith("SELECT"):
            measure["sql_rows"].append(
                {
                    "statement_number": measure["query_count"],
                    "rowcount": cursor.rowcount,
                    "execution_ms": (time.perf_counter() - context._benchmark_start) * 1000,
                    "has_limit": " LIMIT " in statement.replace("\n", " ").upper(),
                    "evidence_query": "cutoff_evidence" in statement,
                    "select_prefix": statement.split("FROM", 1)[0][:180],
                }
            )

    def failed(error):
        measure = CURRENT.get()
        if measure is not None:
            measure["database_error"] = dict(
                type=type(error.original_exception).__name__,
                sqlstate=getattr(error.original_exception, "sqlstate", None),
            )

    sa.event.listen(db, "handle_error", failed)
    sa.event.listen(db, "before_cursor_execute", before)
    sa.event.listen(db, "after_cursor_execute", after)
    originals = {}
    for name in (
        "facts",
        "cutoff",
        "offering",
        "university",
        "sources",
        "university_rows",
        "university_items",
        "offering_rows",
        "offering_items",
        "source_refs",
    ):
        if not hasattr(queries, name):
            continue
        original = getattr(queries, name)
        originals[name] = original

        def counted(c, *args, _name=name, _original=original, **kwargs):
            result = _original(c, *args, **kwargs)
            measure = c.info.get("benchmark")
            if measure is not None:
                key = f"{_name}_calls"
                measure["materialization"][key] = measure["materialization"].get(key, 0) + 1
                if isinstance(result, list):
                    key = f"{_name}_rows"
                    measure["materialization"][key] = measure["materialization"].get(key, 0) + len(
                        result
                    )
                if isinstance(result, dict) and _name == "source_refs":
                    key = "source_refs_rows"
                    measure["materialization"][key] = measure["materialization"].get(key, 0) + sum(
                        len(v) for v in result.values()
                    )
            return result

        setattr(queries, name, counted)

    def snapshot():
        connect_start = time.perf_counter()
        with db.connect().execution_options(isolation_level="REPEATABLE READ") as c, c.begin():
            c.info["benchmark"] = CURRENT.get()
            if c.info["benchmark"] is not None:
                c.info["benchmark"]["db_connect_ms"] = (time.perf_counter() - connect_start) * 1000
                c.info["benchmark"]["pool_checkedout_at_connect"] = db.pool.checkedout()
            try:
                c.exec_driver_sql("SET TRANSACTION READ ONLY")
                c.exec_driver_sql("SET LOCAL statement_timeout='5000ms'")
                if not schema_is_current(c):
                    raise RuntimeError("Synthetic benchmark schema is stale")
                yield c
            finally:
                c.info.pop("benchmark", None)

    app.dependency_overrides[catalog_snapshot] = snapshot
    return originals


def percentile(values, p):
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, max(0, int(len(ordered) * p + 0.999) - 1))]


def request(client, endpoint, params):
    measure = dict(
        query_count=0,
        materialization={},
        sql=[],
        seen_sql=set(),
        query_cap_exceeded=False,
        sql_rows=[],
    )
    measure["endpoint"] = endpoint
    measure["filters"] = {k: v for k, v in params.items() if k != "cursor"}
    measure["has_cursor"] = bool(params.get("cursor"))
    token = CURRENT.set(measure)
    start = time.perf_counter()
    try:
        try:
            response = client.get("/api/v1/" + endpoint, params=params)
        except Exception as error:
            measure["exception"] = dict(
                type=type(error).__name__,
                cause=type(error.__cause__).__name__,
                frames=[
                    f"{Path(f.filename).name}:{f.lineno}:{f.name}"
                    for f in traceback.extract_tb(error.__traceback__)[-5:]
                ],
            )
            response = None
        measure["milliseconds"] = (time.perf_counter() - start) * 1000
        measure["status"] = response.status_code if response is not None else 500
        payload = response.json() if response is not None and response.status_code == 200 else {}
        measure["returned_items"] = len(payload.get("items", []))
        measure["next_cursor"] = payload.get("next_cursor")
        measure["has_more"] = payload.get("has_more")
        measure["coverage_count"] = payload.get("coverage", {}).get("canonical_cutoff_count")
    finally:
        CURRENT.reset(token)
    measure.pop("seen_sql")
    return measure


def summarize(samples):
    latencies = [x["milliseconds"] for x in samples]
    return dict(
        samples=len(samples),
        latency_ms=dict(
            min=min(latencies),
            p50=statistics.median(latencies),
            p95=percentile(latencies, 0.95),
            max=max(latencies),
        ),
        requests=[
            {k: v for k, v in sample.items() if k not in ("sql", "next_cursor")}
            for sample in samples
        ],
    )


def plans(db, statements):
    result = []
    with db.connect() as c, c.begin():
        c.exec_driver_sql("SET TRANSACTION READ ONLY")
        c.exec_driver_sql("SET LOCAL statement_timeout='5000ms'")
        for statement, parameters in statements:
            try:
                with c.begin_nested():
                    plan = c.exec_driver_sql(
                        "EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " + statement, parameters
                    ).scalar_one()
                result.append(dict(sql=statement, plan=plan))
            except sa.exc.SQLAlchemyError as error:
                result.append(dict(sql=statement, error=type(error).__name__))
    return result


def configuration(db):
    keys = (
        "max_connections",
        "shared_buffers",
        "work_mem",
        "effective_cache_size",
        "maintenance_work_mem",
        "random_page_cost",
        "seq_page_cost",
        "max_parallel_workers_per_gather",
        "max_parallel_workers",
        "jit",
    )
    with db.connect() as c:
        settings = {k: c.exec_driver_sql(f"SHOW {k}").scalar_one() for k in keys}
        version = c.exec_driver_sql("SELECT version()").scalar_one()
        size = c.exec_driver_sql("SELECT pg_database_size(current_database())").scalar_one()
        years = [
            dict(r)
            for r in c.exec_driver_sql("""SELECT py.admission_year, count(*) AS facts
            FROM cutoff_scores cs JOIN program_admissions pa ON pa.id=cs.program_admission_id
            JOIN program_years py ON py.id=pa.program_year_id GROUP BY 1 ORDER BY 1""").mappings()
        ]
    return dict(
        database=db.url.database,
        database_bytes=size,
        postgres=version,
        settings=settings,
        years=years,
        machine=dict(
            os=platform.platform(),
            processor=platform.processor(),
            logical_cpus=os.cpu_count(),
            physical_cpus=psutil.cpu_count(logical=False),
            memory_bytes=psutil.virtual_memory().total,
        ),
        catalog_source_sha256={
            name: hashlib.sha256(
                Path(sys.modules[f"services.api.catalog.{name}"].__file__).read_bytes()
            ).hexdigest()
            for name in ("cursor", "dto", "queries", "router")
        },
        pool_size=20,
        max_overflow=0,
    )


def run(args):
    OUTPUT.mkdir(parents=True, exist_ok=True)
    db = prepare(args.database, args.facts, "after" if args.reuse else args.phase)
    if args.phase == "seed":
        write_result(OUTPUT / f"{args.database}-configuration.json", configuration(db))
        db.dispose()
        return
    originals = install_measurement(db, args.query_cap if args.phase == "before" else 0)
    result = dict(
        phase=args.phase,
        started_at=datetime.now(timezone.utc).isoformat(),
        configuration=configuration(db),
        measurement="FastAPI TestClient in process; full read-only RR request including schema check; warm repeated requests; SQL counts include transaction setup",
        baseline_query_cap=args.query_cap if args.phase == "before" else None,
        cases={},
        plans={},
    )
    result["configuration"]["declared_runtime_shm_mib"] = args.runtime_shm_mib
    result["configuration"]["runtime_shm_provenance"] = (
        "Operator-declared Docker /dev/shm allocation; not measured by SQL"
    )
    output = OUTPUT / f"{args.database}-{args.phase}{args.label}.json"
    common = {"year": 2026, "limit": 20}
    cases = []
    for endpoint in ("universities", "programs", "cutoffs"):
        cases.append((endpoint + "_first", endpoint, common))
        filtered = {"method": "SYN0", "campus": "A"}
        if endpoint != "universities":
            filtered["university_id"] = str(synthetic_id("university", 0))
        else:
            filtered["query"] = "Synthetic Alias 0000"
        cases.append((endpoint + "_filtered", endpoint, common | filtered))
        cases.append(
            (endpoint + "_empty", endpoint, common | {"method": "NO-SUCH-SYNTHETIC-METHOD"})
        )
    cases.extend(
        [
            ("programs_search", "programs", common | {"query": "Program 007"}),
            ("programs_search_empty", "programs", common | {"query": "ABSENT%_\\"}),
        ]
    )
    if args.concurrent_only:
        cases = []
    try:
        with TestClient(app, raise_server_exceptions=True) as client:
            for name, endpoint, params in cases:
                samples = []
                for _ in range(args.repeats):
                    sample = request(client, endpoint, params)
                    samples.append(sample)
                    if sample["query_cap_exceeded"] or sample["status"] != 200:
                        break
                result["cases"][name] = summarize(samples)
                result["plans"][name] = plans(db, samples[0]["sql"])
                print(
                    f"{args.phase} {name}: {samples[-1]['status']} {samples[-1]['query_count']} SQL {samples[-1]['milliseconds']:.1f}ms",
                    flush=True,
                )
                if name.endswith("_first") and samples[-1]["next_cursor"]:
                    later_params = params | {"cursor": samples[-1]["next_cursor"]}
                    later = [request(client, endpoint, later_params) for _ in range(args.repeats)]
                    result["cases"][endpoint + "_later"] = summarize(later)
                    result["plans"][endpoint + "_later"] = plans(db, later[0]["sql"])
                write_result(output, result)
            if args.phase == "after" and args.concurrent:
                endpoints = (
                    ("universities", "programs", "cutoffs")
                    if args.concurrent_profile == "lists"
                    else ("universities", "programs")
                )

                def concurrent_params(endpoint):
                    if args.concurrent_profile == "search":
                        return common | {
                            "query": "Synthetic" if endpoint == "universities" else "Program 007"
                        }
                    return common

                concurrent_samples = []
                process = psutil.Process()
                cpu_before = process.cpu_times()
                resource_samples = []
                monitor_stop = threading.Event()
                process.cpu_percent(None)
                psutil.cpu_percent(None)

                def monitor():
                    while not monitor_stop.wait(0.1):
                        resource_samples.append(
                            dict(
                                client_cpu_percent=process.cpu_percent(None),
                                host_cpu_percent=psutil.cpu_percent(None),
                                rss_bytes=process.memory_info().rss,
                                pool_checkedout=db.pool.checkedout(),
                            )
                        )

                monitor_thread = threading.Thread(target=monitor, daemon=True)
                monitor_thread.start()
                start = time.perf_counter()
                with ThreadPoolExecutor(max_workers=args.concurrent) as pool:
                    futures = [
                        pool.submit(
                            request,
                            client,
                            endpoints[i % len(endpoints)],
                            concurrent_params(endpoints[i % len(endpoints)]),
                        )
                        for i in range(args.concurrent * args.rounds)
                    ]
                    for future in futures:
                        concurrent_samples.append(future.result())
                monitor_stop.set()
                monitor_thread.join(timeout=1)
                cpu_after = process.cpu_times()
                result["concurrent"] = summarize(concurrent_samples)
                result["concurrent"]["resources"] = dict(
                    samples=resource_samples,
                    client_cpu_seconds=(
                        cpu_after.user + cpu_after.system - cpu_before.user - cpu_before.system
                    ),
                    note="Python load-generator/API process; host CPU includes Docker and other work; DB CPU not isolated",
                )
                result["concurrent"].update(
                    users=args.concurrent,
                    rounds=args.rounds,
                    elapsed_seconds=time.perf_counter() - start,
                    endpoints=list(endpoints),
                    profile=args.concurrent_profile,
                    queue_model="closed bounded thread pool, requests scheduled upfront",
                )
        result["finished_at"] = datetime.now(timezone.utc).isoformat()
        write_result(output, result)
        print(f"RESULT {output}", flush=True)
    finally:
        app.dependency_overrides.pop(catalog_snapshot, None)
        for name, function in originals.items():
            setattr(queries, name, function)
        db.dispose()


def run_tcp(args):
    """Actual loopback HTTP using an existing reader; grants touch synthetic DB only."""
    from services.api.catalog.roles import provision_reader

    db = prepare(args.database, args.facts, "after")
    with db.begin() as c:
        provision_reader(c)
    credentials = json.loads(Path("state/catalog/access/dev-reader.json").read_text())
    reader = sa.create_engine(
        db.url.set(username=credentials["username"], password=credentials["password"]),
        hide_parameters=True,
    )
    with reader.connect() as c:
        is_superuser = c.scalar(sa.text("SELECT rolsuper FROM pg_roles WHERE rolname=current_user"))
        if is_superuser:
            raise ValueError("TCP benchmark requires the existing non-superuser reader")
    reader.dispose()
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", args.port))
    environment = os.environ.copy()
    environment.update(
        POSTGRES_DB=args.database,
        CATALOG_DB_USER=credentials["username"],
        CATALOG_DB_PASSWORD=credentials["password"],
    )
    if credentials.get("cursor_secret"):
        environment["CATALOG_CURSOR_SECRET"] = credentials["cursor_secret"]
    log_path = OUTPUT / f"{args.database}-tcp-server.log"
    output = OUTPUT / f"{args.database}-tcp-search.json"
    result = dict(
        database=args.database,
        configuration=configuration(db),
        users=args.concurrent,
        rounds=args.rounds,
        transport="urllib HTTP over loopback; uvicorn one process; actual non-superuser reader",
        reader_pool=dict(pool_size=5, max_overflow=10),
        declared_runtime_shm_mib=args.runtime_shm_mib,
    )
    db.dispose()
    base = f"http://127.0.0.1:{args.port}"

    def http_request(number):
        endpoint = ("universities", "programs")[number % 2]
        params = dict(
            year=2026, limit=20, query="Synthetic" if endpoint == "universities" else "Program 007"
        )
        start = time.perf_counter()
        item = dict(endpoint=endpoint, filters=params)
        try:
            with urlopen(
                base + "/api/v1/" + endpoint + "?" + urlencode(params), timeout=30
            ) as response:
                payload = json.load(response)
                item.update(status=response.status, returned_items=len(payload.get("items", [])))
        except HTTPError as error:
            item.update(status=error.code, error=type(error).__name__)
        except Exception as error:
            item.update(status=0, error=type(error).__name__)
        item["milliseconds"] = (time.perf_counter() - start) * 1000
        return item

    with log_path.open("w", encoding="utf-8") as log:
        child = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "services.api.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(args.port),
                "--no-access-log",
            ],
            env=environment,
            stdout=log,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        result.update(
            server_pid=child.pid,
            server_port=args.port,
            started_at=datetime.now(timezone.utc).isoformat(),
        )
        write_result(
            OUTPUT / f"{args.database}-tcp-process.json",
            dict(
                pid=child.pid,
                port=args.port,
                database=args.database,
                log=str(log_path),
                started_at=result["started_at"],
            ),
        )
        try:
            deadline = time.monotonic() + 30
            while True:
                if child.poll() is not None:
                    raise RuntimeError("Synthetic uvicorn exited before readiness")
                try:
                    with urlopen(base + "/health/ready", timeout=2) as response:
                        if response.status == 200:
                            break
                except Exception:
                    if time.monotonic() >= deadline:
                        raise RuntimeError("Synthetic uvicorn readiness timed out") from None
                    time.sleep(0.2)
            warmups = [http_request(0), http_request(1)]
            result["warmups"] = warmups
            runtime_children = psutil.Process(child.pid).children(recursive=True)
            process = runtime_children[-1] if runtime_children else psutil.Process(child.pid)
            result["runtime_server_pid"] = process.pid
            cpu_before = process.cpu_times()
            start = time.perf_counter()
            with ThreadPoolExecutor(max_workers=args.concurrent) as pool:
                samples = list(pool.map(http_request, range(args.concurrent * args.rounds)))
            elapsed = time.perf_counter() - start
            cpu_after = process.cpu_times()
            result.update(
                concurrent=summarize(samples),
                elapsed_seconds=elapsed,
                server_cpu_seconds=cpu_after.user
                + cpu_after.system
                - cpu_before.user
                - cpu_before.system,
                server_rss_bytes=process.memory_info().rss,
            )
        finally:
            descendants = (
                psutil.Process(child.pid).children(recursive=True) if child.poll() is None else []
            )
            child.terminate()
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=5)
            for descendant in descendants:
                try:
                    if descendant.is_running():
                        descendant.terminate()
                        descendant.wait(timeout=5)
                except psutil.NoSuchProcess:
                    pass
            result.update(
                server_exit_code=child.returncode,
                server_stopped=True,
                finished_at=datetime.now(timezone.utc).isoformat(),
            )
            write_result(output, result)
            write_result(
                OUTPUT / f"{args.database}-tcp-process.json",
                dict(
                    pid=child.pid,
                    runtime_pid=result.get("runtime_server_pid"),
                    port=args.port,
                    database=args.database,
                    log=str(log_path),
                    started_at=result["started_at"],
                    stopped=True,
                    stopped_at=result["finished_at"],
                ),
            )
    print(f"RESULT {output}; temporary server PID {child.pid} stopped", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tcp", action="store_true")
    parser.add_argument("--port", type=int, default=3802)
    parser.add_argument("--phase", choices=("before", "after", "seed"), required=True)
    parser.add_argument("--database", type=guarded_name, required=True)
    parser.add_argument("--facts", type=int, default=20_000)
    parser.add_argument("--label", default="", help="Artifact filename suffix")
    parser.add_argument("--runtime-shm-mib", type=int, default=None)
    parser.add_argument("--concurrent-only", action="store_true")
    parser.add_argument("--concurrent-profile", choices=("lists", "search"), default="lists")
    parser.add_argument(
        "--reuse",
        action="store_true",
        help="Read-only rerun of a validated retained synthetic fixture",
    )
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--query-cap", type=int, default=1200)
    parser.add_argument("--concurrent", type=int, default=20)
    parser.add_argument("--rounds", type=int, default=3)
    arguments = parser.parse_args()
    if arguments.tcp:
        run_tcp(arguments)
    else:
        run(arguments)
