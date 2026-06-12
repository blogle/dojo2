from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable

from dojo.benchmark_fixtures import DATASETS, build_synthetic_dataset, describe_dataset
from dojo.database import Database
from dojo.service import DojoService


@dataclass
class BenchmarkResult:
    operation: str
    dataset_label: str
    duration_ms: float
    row_count: int
    total_rows: int
    payload_bytes: int | None = None
    notes: str = ""


@dataclass
class ExplainAnalyzeResult:
    query: str
    plan: str
    duration_ms: float


class Timer:
    def __init__(self) -> None:
        self.start: float = 0.0
        self.elapsed_ms: float = 0.0

    def __enter__(self) -> Timer:
        self.start = time.perf_counter()
        return self

    def __exit__(self, *args: Any) -> None:
        self.elapsed_ms = (time.perf_counter() - self.start) * 1000


def explain_analyze(db: Database, query: str, params: tuple[Any, ...] = ()) -> ExplainAnalyzeResult:
    plan_rows = db.fetch_all(f"EXPLAIN ANALYZE {query}", params) if params else db.fetch_all(f"EXPLAIN ANALYZE {query}")
    plan_text = "\n".join(row.get("explain_key", "") if "explain_key" in row else list(row.values())[0] for row in plan_rows)
    duration_str = ""
    for line in plan_text.split("\n"):
        if "EC" in line and "rows" in line:
            for part in line.split():
                if part.endswith("s") and part[:-1].replace(".", "").isdigit():
                    duration_str = part[:-1]
    duration_ms = float(duration_str) * 1000 if duration_str else 0.0
    return ExplainAnalyzeResult(query=query, plan=plan_text, duration_ms=duration_ms)


def _create_benchmark_service(config: Any) -> DojoService:
    bundle = build_synthetic_dataset(config)
    service = DojoService(":memory:")
    imported_at = __import__("dojo.scd", fromlist=["utc_now"]).utc_now()
    with service.db.transaction() as connection:
        service._clear_domain_tables(connection)
        service._insert_bundle(connection, bundle, imported_at)
    return service


def run_backend_benchmarks() -> list[list[BenchmarkResult]]:
    all_results: list[list[BenchmarkResult]] = []
    for config in DATASETS:
        results = _run_single_dataset(config)
        all_results.append(results)
    return all_results


def _run_single_dataset(config: Any) -> list[BenchmarkResult]:
    t = Timer()
    with t:
        service = _create_benchmark_service(config)
    ds = describe_dataset(bundle_for(config))
    tx_count = ds["transactions"]

    results: list[BenchmarkResult] = []

    # Helper to run a benchmark
    def bench(
        op: str,
        fn: Callable[[], Any],
        *,
        row_extractor: Callable[[Any], int] | None = None,
        total_rows: int = 0,
        payload_extractor: Callable[[Any], int] | None = None,
    ) -> None:
        with t:
            result = fn()
        count = row_extractor(result) if row_extractor else 0
        payload = payload_extractor(result) if payload_extractor else None
        results.append(
            BenchmarkResult(
                operation=op,
                dataset_label=config.label,
                duration_ms=t.elapsed_ms,
                row_count=count,
                total_rows=total_rows or count,
                payload_bytes=payload,
            )
        )

        # Transaction list queries
        for limit in (50, 500, 2000):
            bench(
                f"list_transactions(limit={limit})",
                lambda lim=limit: service.list_transactions(limit=lim, show_hidden=True),
                row_extractor=lambda r: len(r["items"]),
                total_rows=tx_count,
            )

    # Account balance query
    bench(
        "list_accounts",
        lambda: service.list_accounts(show_hidden=True),
        row_extractor=lambda r: len(r),
        total_rows=ds["accounts"],
    )

    # Category queries
    month = service.default_budget_month()
    bench(
        "list_categories",
        lambda m=month: service.list_categories(month=m, show_hidden=True),
        row_extractor=lambda r: len(r),
        total_rows=ds["categories"],
    )

    bench(
        "list_category_groups",
        lambda m=month: service.list_category_groups(month=m, show_hidden=True),
        row_extractor=lambda r: len(r),
        total_rows=ds["groups"],
    )

    # Full budget
    bench(
        "get_budget",
        lambda m=month: service.get_budget(m, show_hidden=True),
        row_extractor=lambda r: len(r.get("groups", [])),
        total_rows=ds["groups"],
    )

    # ATB computation
    bench(
        "compute_available_to_budget",
        lambda: service.compute_available_to_budget(),
        row_extractor=lambda r: 1,
        total_rows=1,
    )

    # Category-level computations
    categories = service.list_categories(month=month, show_hidden=True)
    if categories:
        cat = categories[0]
        ms, me = service._month_bounds(month)
        bench(
            "compute_category_available (single)",
            lambda cid=cat["category_id"]: service.compute_category_available(cid),
            row_extractor=lambda r: 1,
            total_rows=1,
        )
        bench(
            "compute_month_activity (single)",
            lambda cid=cat["category_id"], ms=ms, me=me: service.compute_month_activity(cid, ms, me),
            row_extractor=lambda r: 1,
            total_rows=1,
        )
        bench(
            "compute_month_budgeted (single)",
            lambda bid=cat["bucket_id"], ms=ms, me=me: service.compute_month_budgeted(bid, ms, me),
            row_extractor=lambda r: 1,
            total_rows=1,
        )
        bench(
            "compute_carried_over (single)",
            lambda cid=cat["category_id"], bid=cat["bucket_id"], ms=ms: service.compute_carried_over(cid, bid, ms),
            row_extractor=lambda r: 1,
            total_rows=1,
        )

    # Reportable income / spent
    bench(
        "compute_reportable_income",
        lambda ms=ms, me=me: service.compute_reportable_income(ms, me),
        row_extractor=lambda r: 1,
        total_rows=1,
    )
    bench(
        "compute_spent",
        lambda ms=ms, me=me: service.compute_spent(ms, me, show_hidden=True),
        row_extractor=lambda r: 1,
        total_rows=1,
    )

    # Net worth
    bench(
        "get_net_worth",
        lambda: service.get_net_worth(),
        row_extractor=lambda r: len(r.get("items", [])),
        total_rows=ds["accounts"] + ds["valuations"],
    )

    # Snapshot for validation (used after import)
    months = list(ds["months"])
    if months:
        bench(
            "snapshot_for_validation",
            lambda m=months: service.snapshot_for_validation(m),
            row_extractor=lambda r: r.get("account_count", 0),
            total_rows=ds["accounts"],
        )

    service.close()
    return results


def bundle_for(config: Any) -> Any:
    return build_synthetic_dataset(config)


def format_results_table(all_results: list[list[BenchmarkResult]]) -> str:
    lines = ["# dojo Backend Benchmarks", "", "## Dataset Summary"]
    for _, config in enumerate(DATASETS):
        ds = describe_dataset(bundle_for(config))
        lines.append(
            f"\n### {config.label}: {ds['transactions']} transactions, "
            f"{ds['accounts']} accounts, {ds['categories']} categories, "
            f"{len(ds['months'])} months, {ds['allocations']} allocations"
        )

    lines.append("\n\n## Per-Operation Timings")
    lines.append(f"{'Operation':<55} {'1K (ms)':<12} {'10K (ms)':<12} {'100K (ms)':<12} {'Notes':<20}")
    lines.append("-" * 111)

    if not all_results:
        return "\n".join(lines)

    ops = [r.operation for r in all_results[0]]
    for op_idx, op_name in enumerate(ops):
        row = f"{op_name:<55}"
        for dataset_idx in range(len(all_results)):
            r = all_results[dataset_idx][op_idx]
            row += f"{r.duration_ms:<12.2f}"
        lines.append(row)

    lines.append("")
    lines.append("*Measured on synthetic datasets. Timings are wall-clock in milliseconds.*")
    return "\n".join(lines)


def run_and_print() -> None:
    print("Building synthetic datasets and running benchmarks...")
    results = run_backend_benchmarks()
    table = format_results_table(results)
    print(table)


if __name__ == "__main__":
    run_and_print()
