from __future__ import annotations

import json
from importlib import reload
from typing import Any

import pytest
from fastapi.testclient import TestClient

import dojo.api.main as main_module
from dojo.api.settings import get_settings
from dojo.benchmark_fixtures import (
    DATASET_MEDIUM,
    DATASET_SMALL,
    DATASETS,
    build_synthetic_dataset,
    describe_dataset,
)
from dojo.benchmarks import (
    Timer,
    _create_benchmark_service,
    explain_analyze,
    payload_size_bytes,
    profile_import,
    run_backend_benchmarks,
)
from dojo.migrations import provision_database


class TestBackendBenchmarks:
    """Backend query and formula benchmarks.

    These are wall-clock benchmarks on synthetic datasets. They report timings
    and row counts rather than asserting hard pass/fail thresholds.
    """

    @pytest.mark.parametrize("dataset_config", DATASETS, ids=lambda c: c.label)
    def test_dataset_creation(self, dataset_config) -> None:
        """Verify synthetic datasets build correctly with expected row counts."""
        bundle = build_synthetic_dataset(dataset_config)
        ds = describe_dataset(bundle)
        assert ds["transactions"] == dataset_config.num_transactions
        assert ds["accounts"] == dataset_config.num_accounts
        assert ds["categories"] == dataset_config.num_categories
        assert len(ds["months"]) <= dataset_config.num_months

    @pytest.mark.parametrize("dataset_config", [DATASET_SMALL], ids=["1K"])
    def test_import_speed(self, dataset_config) -> None:
        """Measure how long it takes to import the synthetic dataset."""
        with Timer() as t:
            service = _create_benchmark_service(dataset_config)
        service.close()
        print(
            f"\nImport {dataset_config.label}: {t.elapsed_ms:.2f}ms for {dataset_config.num_transactions} tx"
        )

    @pytest.mark.parametrize("dataset_config", [DATASET_SMALL, DATASET_MEDIUM], ids=["1K", "10K"])
    def test_import_profile(self, dataset_config) -> None:
        """Print import phase timings for realistic synthetic dataset sizes."""
        profile = profile_import(dataset_config)
        phase_lines = ", ".join(
            f"{name}={duration:.2f}ms"
            for name, duration in sorted(
                profile.phase_timings_ms.items(), key=lambda item: item[1], reverse=True
            )
        )
        print(
            f"\nImport profile {profile.dataset_label}: {profile.total_ms:.2f}ms total "
            f"({profile.transaction_count} tx, {profile.allocation_count} allocations, {profile.valuation_count} valuations)"
        )
        print(phase_lines)
        assert profile.transaction_count == dataset_config.num_transactions

    @pytest.mark.parametrize("dataset_config", [DATASET_SMALL], ids=["1K"])
    def test_list_transactions_benchmark(self, dataset_config) -> None:
        """Benchmark list_transactions at various limit sizes."""
        service = _create_benchmark_service(dataset_config)

        for limit in (50, 500):
            with Timer() as t:
                result = service.list_transactions(limit=limit, show_hidden=True)
            items = result["items"]
            print(
                f"\nlist_transactions(limit={limit}): {t.elapsed_ms:.2f}ms"
                f" ({len(items)}/{dataset_config.num_transactions} rows)"
            )
            assert len(items) <= limit
        service.close()

    @pytest.mark.parametrize("dataset_config", [DATASET_SMALL, DATASET_MEDIUM], ids=["1K", "10K"])
    def test_transaction_window_payload_benchmark(self, dataset_config) -> None:
        """Measure bounded transaction-page payload size on realistic ledgers."""
        service = _create_benchmark_service(dataset_config)

        for offset in (0, 100):
            with Timer() as t:
                result = service.list_transactions(
                    limit=100,
                    offset=offset,
                    show_hidden=True,
                )
            payload_bytes = payload_size_bytes(result)
            print(
                f"\ntransaction window {dataset_config.label}: offset={offset} limit=100 "
                f"{t.elapsed_ms:.2f}ms ({len(result['items'])} rows, {payload_bytes} bytes, total={result['total']})"
            )
            assert len(result["items"]) <= 100
            assert result["limit"] == 100
            assert result["offset"] == offset
        service.close()

    @pytest.mark.parametrize("dataset_config", [DATASET_SMALL], ids=["1K"])
    def test_list_categories_benchmark(self, dataset_config) -> None:
        """Benchmark list_categories which has N+1 query characteristics."""
        service = _create_benchmark_service(dataset_config)

        month = service.default_budget_month()
        with Timer() as t:
            result = service.list_categories(month=month, show_hidden=True)
        print(f"\nlist_categories: {t.elapsed_ms:.2f}ms ({len(result)} categories)")
        assert len(result) == dataset_config.num_categories
        service.close()

    @pytest.mark.parametrize("dataset_config", [DATASET_SMALL], ids=["1K"])
    def test_get_budget_benchmark(self, dataset_config) -> None:
        """Benchmark full get_budget (most expensive aggregate endpoint)."""
        service = _create_benchmark_service(dataset_config)

        month = service.default_budget_month()
        with Timer() as t:
            result = service.get_budget(month, show_hidden=True)
        print(f"\nget_budget: {t.elapsed_ms:.2f}ms")
        assert "available_to_budget_minor" in result
        assert "groups" in result
        service.close()

    @pytest.mark.parametrize("dataset_config", [DATASET_SMALL, DATASET_MEDIUM], ids=["1K", "10K"])
    def test_budget_shape_benchmark(self, dataset_config) -> None:
        """Measure category, group, and budget shaping without duplicated aggregation."""
        service = _create_benchmark_service(dataset_config)

        month = service.default_budget_month()
        with Timer() as category_timer:
            categories = service.list_categories(month=month, show_hidden=True)
        with Timer() as grouped_timer:
            groups = service.list_category_groups(
                month=month,
                show_hidden=True,
                precomputed_categories=categories,
            )
        with Timer() as budget_timer:
            budget = service.get_budget(month, show_hidden=True)
        print(
            f"\nbudget shape {dataset_config.label}: categories={category_timer.elapsed_ms:.2f}ms, "
            f"groups_from_precomputed={grouped_timer.elapsed_ms:.2f}ms, "
            f"get_budget={budget_timer.elapsed_ms:.2f}ms"
        )
        assert len(groups) == len(budget["groups"])
        service.close()

    @pytest.mark.parametrize("dataset_config", [DATASET_SMALL], ids=["1K"])
    def test_explain_analyze_transactions(self, dataset_config) -> None:
        """Use EXPLAIN ANALYZE to measure query execution time vs Python time."""
        service = _create_benchmark_service(dataset_config)

        # Measure raw query time
        explain = explain_analyze(
            service.db,
            "SELECT * FROM current_transactions ORDER BY date DESC",
        )
        print(f"\nEXPLAIN ANALYZE (full tx scan): {explain.duration_ms:.2f}ms query")

        # Measure total handler time for same query
        with Timer() as t:
            rows = service.db.fetch_all("SELECT * FROM current_transactions ORDER BY date DESC")
        print(f"Total fetch + serialize: {t.elapsed_ms:.2f}ms ({len(rows)} rows)")
        service.close()

    @pytest.mark.parametrize("dataset_config", [DATASET_SMALL], ids=["1K"])
    def test_account_balances_benchmark(self, dataset_config) -> None:
        """Benchmark account balance calculation."""
        service = _create_benchmark_service(dataset_config)

        with Timer() as t:
            result = service.list_accounts(show_hidden=True)
        print(f"\nlist_accounts: {t.elapsed_ms:.2f}ms ({len(result)} accounts)")
        service.close()

    @pytest.mark.parametrize("dataset_config", [DATASET_SMALL], ids=["1K"])
    def test_atb_benchmark(self, dataset_config) -> None:
        """Benchmark Available to Budget computation."""
        service = _create_benchmark_service(dataset_config)

        with Timer() as t:
            atb = service.compute_available_to_budget()
        print(f"\ncompute_available_to_budget: {t.elapsed_ms:.2f}ms (result: {atb})")
        service.close()

    @pytest.mark.parametrize("dataset_config", [DATASET_SMALL], ids=["1K"])
    def test_net_worth_benchmark(self, dataset_config) -> None:
        """Benchmark net worth computation."""
        service = _create_benchmark_service(dataset_config)

        with Timer() as t:
            result = service.get_net_worth()
        print(f"\nget_net_worth: {t.elapsed_ms:.2f}ms ({len(result.get('items', []))} items)")
        service.close()

    @pytest.mark.parametrize("dataset_config", [DATASET_SMALL, DATASET_MEDIUM], ids=["1K", "10K"])
    def test_bootstrap_payload_benchmark(self, dataset_config) -> None:
        """Measure bootstrap latency and payload growth by dataset size."""
        service = _create_benchmark_service(dataset_config)

        with Timer() as t:
            bootstrap = service.get_bootstrap()
        payload_bytes = payload_size_bytes(bootstrap)
        print(
            f"\nget_bootstrap {dataset_config.label}: {t.elapsed_ms:.2f}ms "
            f"({payload_bytes} bytes, keys={sorted(bootstrap.keys())})"
        )
        assert payload_bytes > 0
        service.close()

    @pytest.mark.skip(reason="Manual-only: runs all datasets including 100K (>2min)")
    def test_full_backend_benchmark_suite(self) -> None:
        """Run all benchmarks across all dataset sizes and print report."""
        results = run_backend_benchmarks()
        from dojo.benchmarks import format_results_table

        table = format_results_table(results)
        print(f"\n\n{table}")


class TestApiBenchmarks:
    """API route-level benchmarks with timing and payload measurement."""

    def _build_environ(self, tmp_path) -> None:
        import os

        duckdb_path = tmp_path / "bench-api.duckdb"
        os.environ["DUCKDB_PATH"] = str(duckdb_path)
        os.environ["SESSION_SECRET"] = "bench-secret"
        os.environ["DEV_FIXTURE_MODE"] = "true"
        os.environ["GOOGLE_OAUTH_REDIRECT_URI"] = (
            "http://localhost:8000/api/onboarding/google/callback"
        )
        provision_database(str(duckdb_path))
        get_settings.cache_clear()
        reload(main_module)

    def _bench_get(
        self, client: TestClient, path: str, label: str, params: dict[str, Any] | None = None
    ) -> None:
        with Timer() as t:
            response = client.get(path, params=params)
        body = response.json()
        body_str = json.dumps(body)
        items = body.get("items") or body.get("groups") or [body]
        row_count = len(items) if isinstance(items, list) else 1
        print(
            f"\n{label}: {t.elapsed_ms:.2f}ms "
            f"({row_count} items, {len(body_str)} bytes, status={response.status_code})"
        )

    def _run_with_client(self, tmp_path, fn) -> None:
        self._build_environ(tmp_path)
        with TestClient(main_module.app) as client:
            fn(client)

    def test_api_transactions_benchmark(self, tmp_path) -> None:
        """Benchmark GET /api/transactions with endpoint timing and payload size."""

        def run(client):
            client.post("/api/import/google-sheet", json={"sheet_url_or_id": "fixture://default"})
            for limit in (20, 100, 500):
                self._bench_get(
                    client,
                    "/api/transactions",
                    f"GET /api/transactions?limit={limit}",
                    params={"limit": limit, "show_hidden": "true"},
                )

        self._run_with_client(tmp_path, run)

    def test_api_budget_benchmark(self, tmp_path) -> None:
        """Benchmark GET /api/budget."""

        def run(client):
            client.post("/api/import/google-sheet", json={"sheet_url_or_id": "fixture://default"})
            self._bench_get(
                client,
                "/api/budget",
                "GET /api/budget",
                params={"month": "2026-02", "show_hidden": "true"},
            )

        self._run_with_client(tmp_path, run)

    def test_api_accounts_benchmark(self, tmp_path) -> None:
        """Benchmark GET /api/accounts."""

        def run(client):
            client.post("/api/import/google-sheet", json={"sheet_url_or_id": "fixture://default"})
            self._bench_get(
                client, "/api/accounts", "GET /api/accounts", params={"show_hidden": "true"}
            )

        self._run_with_client(tmp_path, run)

    def test_api_categories_benchmark(self, tmp_path) -> None:
        """Benchmark GET /api/categories."""

        def run(client):
            client.post("/api/import/google-sheet", json={"sheet_url_or_id": "fixture://default"})
            self._bench_get(
                client,
                "/api/categories",
                "GET /api/categories",
                params={"month": "2026-02", "show_hidden": "true"},
            )

        self._run_with_client(tmp_path, run)

    def test_api_net_worth_benchmark(self, tmp_path) -> None:
        """Benchmark GET /api/net-worth."""

        def run(client):
            client.post("/api/import/google-sheet", json={"sheet_url_or_id": "fixture://default"})
            self._bench_get(client, "/api/net-worth", "GET /api/net-worth")

        self._run_with_client(tmp_path, run)

    def test_api_bootstrap_benchmark(self, tmp_path) -> None:
        """Benchmark GET /api/bootstrap (the most expensive initial load)."""

        def run(client):
            client.post("/api/import/google-sheet", json={"sheet_url_or_id": "fixture://default"})
            self._bench_get(client, "/api/bootstrap", "GET /api/bootstrap")

        self._run_with_client(tmp_path, run)

    def test_api_payload_size_report(self, tmp_path) -> None:
        """Print payload sizes for all major endpoints."""

        def run(client):
            client.post("/api/import/google-sheet", json={"sheet_url_or_id": "fixture://default"})

            endpoints = [
                (
                    "GET /api/transactions?limit=50",
                    "/api/transactions",
                    {"limit": "50", "show_hidden": "true"},
                ),
                (
                    "GET /api/transactions?limit=500",
                    "/api/transactions",
                    {"limit": "500", "show_hidden": "true"},
                ),
                ("GET /api/budget", "/api/budget", {"month": "2026-02", "show_hidden": "true"}),
                ("GET /api/accounts", "/api/accounts", {"show_hidden": "true"}),
                (
                    "GET /api/categories",
                    "/api/categories",
                    {"month": "2026-02", "show_hidden": "true"},
                ),
                ("GET /api/net-worth", "/api/net-worth", None),
                ("GET /api/bootstrap", "/api/bootstrap", None),
            ]

            print("\n\nAPI Payload Size Report:")
            print(f"{'Endpoint':<50} {'Rows':<10} {'Bytes':<10}")
            print("-" * 70)
            for label, path, params in endpoints:
                resp = client.get(path, params=params)
                body = resp.json()
                body_str = json.dumps(body)
                items = body.get("items") or body.get("groups") or [body]
                row_count = len(items) if isinstance(items, list) else 1
                print(f"{label:<50} {row_count:<10} {len(body_str):<10}")

        self._run_with_client(tmp_path, run)
