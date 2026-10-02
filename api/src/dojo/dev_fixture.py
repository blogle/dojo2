from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, cast

from dojo.clock import FrozenClock
from dojo.database import Database
from dojo.fixture_data import DEFAULT_FIXTURE
from dojo.importer import NamedRangeMatrix
from dojo.migrations import apply_migrations
from dojo.service import DojoService

FIXTURE_TIME = datetime(2026, 7, 1, 12, tzinfo=timezone.utc)


def build_development_database(output_path: str | Path) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.unlink(missing_ok=True)

    database = Database(str(output))
    try:
        apply_migrations(database.connection)
    finally:
        database.close()

    fixture = cast(dict[str, Any], DEFAULT_FIXTURE)
    service = DojoService(
        str(output),
        clock=FrozenClock(FIXTURE_TIME, business_date=date(2026, 7, 1)),
    )
    try:
        result = service.import_sheet_data(
            source="synthetic-development-fixture",
            source_kind="development_fixture",
            spreadsheet_title=cast(str, fixture["spreadsheet_title"]),
            named_ranges=cast(dict[str, NamedRangeMatrix], fixture["named_ranges"]),
            expected=cast(dict[str, Any], fixture["expected"]),
        )
        if not result["ok"]:
            raise RuntimeError("Development fixture failed aggregate validation")
    finally:
        service.close()
    return output


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a deterministic dojo development database"
    )
    parser.add_argument("output_path", help="DuckDB file to create or replace")
    args = parser.parse_args()
    print(build_development_database(args.output_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
