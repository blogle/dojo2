from __future__ import annotations

import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from dojo.importer import parse_named_range_workbook
from dojo.migrations import provision_database
from dojo.service import DojoService


def main() -> int:
    parser = argparse.ArgumentParser(description="Run dojo aggregate validation")
    parser.add_argument(
        "--fixture", action="store_true", help="Validate the deterministic repository fixture"
    )
    parser.add_argument(
        "--fetch-dump",
        help="Validate a saved live-sheet fetch dump produced by dojo.live_sheet_harness",
    )
    parser.add_argument(
        "--duckdb-path",
        help="Optional DuckDB path to reuse instead of a temporary file",
    )
    parser.add_argument(
        "--reviewed",
        action="store_true",
        help="Exercise the analyze/review/commit path instead of direct import",
    )
    args = parser.parse_args()

    if bool(args.fixture) == bool(args.fetch_dump):
        raise SystemExit("Choose exactly one of --fixture or --fetch-dump")

    if args.duckdb_path:
        report = run_validation(args, Path(args.duckdb_path))
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["passed"] else 1

    with TemporaryDirectory(prefix="dojo-aggregate-validation-") as temp_dir:
        report = run_validation(args, Path(temp_dir) / "validation.duckdb")
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["passed"] else 1


def run_validation(args: argparse.Namespace, duckdb_path: Path) -> dict[str, Any]:
    provision_database(str(duckdb_path))
    service = DojoService(str(duckdb_path))
    try:
        if args.fixture:
            if args.reviewed:
                return _run_reviewed_validation(
                    service, source="fixture://default", source_kind="fixture"
                )
            result = service.import_sheet_data(source="fixture://default", source_kind="fixture")
            return dict(result["validation_report"])

        payload = json.loads(Path(args.fetch_dump).read_text())
        bundle = parse_named_range_workbook(
            spreadsheet_id=payload["spreadsheet_id"],
            spreadsheet_title=payload["spreadsheet_title"],
            named_ranges=payload["named_ranges"],
            available_named_ranges=payload.get("available_named_ranges"),
            source_kind="google_sheets",
        )
        if args.reviewed:
            return _run_reviewed_validation(
                service,
                source=payload["spreadsheet_id"],
                source_kind="google_sheets",
                spreadsheet_title=bundle.spreadsheet_title,
                named_ranges=payload["named_ranges"],
                available_named_ranges=payload.get("available_named_ranges"),
            )
        result = service.import_sheet_data(
            source=payload["spreadsheet_id"],
            source_kind="google_sheets",
            spreadsheet_title=bundle.spreadsheet_title,
            named_ranges=payload["named_ranges"],
            available_named_ranges=payload.get("available_named_ranges"),
        )
        return dict(result["validation_report"])
    finally:
        service.close()


def _run_reviewed_validation(
    service: DojoService,
    *,
    source: str,
    source_kind: str,
    spreadsheet_title: str | None = None,
    named_ranges: dict[str, list[list[str]]] | None = None,
    available_named_ranges: list[str] | None = None,
) -> dict[str, Any]:
    preview = service.analyze_import_draft(
        source=source,
        source_kind=source_kind,
        spreadsheet_title=spreadsheet_title,
        named_ranges=named_ranges,
        available_named_ranges=available_named_ranges,
    )
    decisions = [
        {
            "raw_name": item["raw_name"],
            "treatment": item["suggested_treatment"],
            "matched_account_id": item["suggested_matched_account_id"],
            "polarity": item["suggested_polarity"],
        }
        for item in preview["review_items"]
    ]
    result = service.commit_import_draft(
        draft_id=str(preview["draft_id"]),
        decisions=decisions,
        low_confidence_confirmed=True,
    )
    return dict(result["validation_report"])


if __name__ == "__main__":
    raise SystemExit(main())
