from __future__ import annotations

import hashlib
import json
import os
import shutil
from argparse import ArgumentParser
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from importlib.metadata import version
from pathlib import Path
from time import perf_counter

from dojo.clock import FrozenClock
from dojo.database import Database
from dojo.migrations import apply_migrations
from dojo.sql import SQL_ROOT, load_sql

E2E_FIXED_TIME = datetime(2026, 2, 15, 12, 0, tzinfo=timezone.utc)


class E2EScenario(StrEnum):
    ASSETS_LIABILITIES_OVERVIEW = "assets-liabilities-overview"
    TANGIBLE_ASSET_CREATION = "tangible-asset-creation"
    TRACKING_SNAPSHOT_CORRECTION = "tracking-snapshot-correction"
    CASH_ONLY_INVESTMENT = "cash-only-investment"


@dataclass(frozen=True, slots=True)
class E2EFixture:
    scenario: E2EScenario
    fingerprint: str
    path: Path


@dataclass(frozen=True, slots=True)
class E2EResetMetrics:
    scenario: E2EScenario
    fixture_fingerprint: str
    fixed_time: datetime
    db_bytes: int
    restore_ms: float
    reopen_ms: float


def fixed_e2e_clock() -> FrozenClock:
    return FrozenClock(E2E_FIXED_TIME, business_date=E2E_FIXED_TIME.date())


def fixture_sql(scenario: E2EScenario) -> tuple[str, ...]:
    scenario_sql = {
        E2EScenario.ASSETS_LIABILITIES_OVERVIEW: ("tests/e2e/scenarios/al_01_overview",),
        E2EScenario.TANGIBLE_ASSET_CREATION: ("tests/e2e/scenarios/al_02_tangible_creation",),
        E2EScenario.TRACKING_SNAPSHOT_CORRECTION: (
            "tests/e2e/scenarios/al_03_tracking_correction",
        ),
        E2EScenario.CASH_ONLY_INVESTMENT: ("tests/e2e/scenarios/al_04_cash_only_investment",),
    }
    return ("tests/e2e/core", *scenario_sql[scenario])


def fixture_fingerprint(scenario: E2EScenario) -> str:
    fingerprint = hashlib.sha256()
    fingerprint.update(version("duckdb").encode("utf-8"))
    fingerprint.update(Path(__file__).with_name("migrations.py").read_bytes())
    for path in sorted((SQL_ROOT / "schema").rglob("*.sql")):
        fingerprint.update(str(path.relative_to(SQL_ROOT)).encode("utf-8"))
        fingerprint.update(path.read_bytes())
    for sql_name in fixture_sql(scenario):
        fingerprint.update(sql_name.encode("utf-8"))
        fingerprint.update(load_sql(sql_name).encode("utf-8"))
    return fingerprint.hexdigest()


def build_baseline(scenario: E2EScenario, output_path: str | Path) -> E2EFixture:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.unlink(missing_ok=True)
    sql_names = fixture_sql(scenario)
    fingerprint = fixture_fingerprint(scenario)
    database = Database(str(output))
    try:
        apply_migrations(database.connection)
        with database.transaction() as connection:
            for sql_name in sql_names:
                connection.execute(load_sql(sql_name))
    finally:
        database.close()
    return E2EFixture(scenario, fingerprint, output)


def stage_baseline(baseline: Path, database_path: Path) -> Path:
    if baseline.resolve() == database_path.resolve():
        raise ValueError("E2E baseline and active database paths must differ")
    database_path.parent.mkdir(parents=True, exist_ok=True)
    staged = database_path.with_name(f".{database_path.name}.resetting")
    shutil.copyfile(baseline, staged)
    return staged


def activate_staged_baseline(staged: Path, database_path: Path) -> int:
    os.replace(staged, database_path)
    return database_path.stat().st_size


def baseline_path(baseline_dir: str | Path, scenario: E2EScenario) -> Path:
    return Path(baseline_dir) / f"{scenario.value}.duckdb"


def main() -> int:
    parser = ArgumentParser(description="Build a deterministic dojo E2E database baseline")
    parser.add_argument("scenario", choices=[scenario.value for scenario in E2EScenario])
    parser.add_argument("output_path")
    args = parser.parse_args()

    scenario = E2EScenario(args.scenario)
    output = Path(args.output_path)
    metadata_path = output.with_suffix(f"{output.suffix}.json")
    fingerprint = fixture_fingerprint(scenario)
    started = perf_counter()
    cache_hit = False
    if output.is_file() and metadata_path.is_file():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        cache_hit = metadata.get("fixture_fingerprint") == fingerprint
    fixture = (
        E2EFixture(scenario, fingerprint, output) if cache_hit else build_baseline(scenario, output)
    )
    duration_ms = (perf_counter() - started) * 1000
    result = {
        "scenario": fixture.scenario.value,
        "fixture_fingerprint": fixture.fingerprint,
        "path": str(fixture.path),
        "db_bytes": fixture.path.stat().st_size,
        "generation_ms": duration_ms,
        "cache_hit": cache_hit,
    }
    metadata_path.write_text(json.dumps(result, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
