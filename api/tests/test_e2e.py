from __future__ import annotations

import shutil
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from fastapi.testclient import TestClient

from dojo.api.main import create_app
from dojo.api.settings import Settings
from dojo.e2e import E2EScenario, build_baseline, fixed_e2e_clock
from dojo.service import DojoService


def test_al_01_fixture_contract(tmp_path) -> None:
    baseline = tmp_path / "assets-liabilities-overview.duckdb"
    fixture = build_baseline(E2EScenario.ASSETS_LIABILITIES_OVERVIEW, baseline)

    service = DojoService(str(fixture.path), clock=fixed_e2e_clock())
    try:
        overview = service.get_assets_liabilities()
        assert overview["assets_minor"] == 56_100_000
        assert overview["liabilities_minor"] == -20_000_000
        assert overview["net_worth_minor"] == 36_100_000
        assert service.get_net_worth()["current_net_worth_minor"] == 36_100_000
    finally:
        service.close()


def test_e2e_reset_route_is_absent_outside_e2e(tmp_path) -> None:
    database_path = tmp_path / "development.duckdb"
    build_baseline(E2EScenario.ASSETS_LIABILITIES_OVERVIEW, database_path)
    app = create_app(Settings(DUCKDB_PATH=str(database_path), APP_ENV="development"))

    with TestClient(app) as client:
        response = client.post(
            "/__e2e/reset",
            headers={"X-Dojo-E2E-Token": "not-available"},
            json={"scenario": E2EScenario.ASSETS_LIABILITIES_OVERVIEW.value},
        )

    assert response.status_code == 404


def test_e2e_reset_is_token_protected_repeatable_and_measured(tmp_path) -> None:
    baseline_dir = tmp_path / "baselines"
    baseline = baseline_dir / "assets-liabilities-overview.duckdb"
    active_database = tmp_path / "worker.duckdb"
    sentinel = tmp_path / ".dojo-e2e-worker"
    build_baseline(E2EScenario.ASSETS_LIABILITIES_OVERVIEW, baseline)
    shutil.copyfile(baseline, active_database)
    sentinel.write_text("acceptance-secret", encoding="utf-8")

    settings = Settings(
        APP_ENV="e2e",
        DUCKDB_PATH=str(active_database),
        E2E_BASELINE_DIR=str(baseline_dir),
        E2E_RUN_DIR=str(tmp_path),
        E2E_RESET_TOKEN="acceptance-secret",
    )
    app = create_app(settings)

    with TestClient(app) as client:
        forbidden = client.post(
            "/__e2e/reset",
            json={"scenario": E2EScenario.ASSETS_LIABILITIES_OVERVIEW.value},
        )
        assert forbidden.status_code == 403

        unknown = client.post(
            "/__e2e/reset",
            headers={"X-Dojo-E2E-Token": "acceptance-secret"},
            json={"scenario": "unknown"},
        )
        assert unknown.status_code == 422

        for _ in range(2):
            reset = client.post(
                "/__e2e/reset",
                headers={"X-Dojo-E2E-Token": "acceptance-secret"},
                json={"scenario": E2EScenario.ASSETS_LIABILITIES_OVERVIEW.value},
            )
            assert reset.status_code == 200
            payload = reset.json()
            assert payload["scenario"] == "assets-liabilities-overview"
            assert payload["fixture_fingerprint"]
            assert payload["fixed_time"] == "2026-02-15T12:00:00+00:00"
            assert payload["db_bytes"] > 0
            assert payload["restore_ms"] >= 0
            assert payload["reopen_ms"] >= 0

            overview = client.get("/api/assets-liabilities")
            assert overview.status_code == 200
            assert overview.json()["net_worth_minor"] == 36_100_000

        start = Barrier(3)

        def read_overview() -> int:
            start.wait()
            return client.get("/api/assets-liabilities").status_code

        def reset_database() -> int:
            start.wait()
            return client.post(
                "/__e2e/reset",
                headers={"X-Dojo-E2E-Token": "acceptance-secret"},
                json={"scenario": E2EScenario.ASSETS_LIABILITIES_OVERVIEW.value},
            ).status_code

        with ThreadPoolExecutor(max_workers=2) as executor:
            read_result = executor.submit(read_overview)
            reset_result = executor.submit(reset_database)
            start.wait()
            assert {read_result.result(), reset_result.result()} == {200}


def test_e2e_reset_rejects_a_database_outside_the_worker_directory(tmp_path) -> None:
    baseline_dir = tmp_path / "baselines"
    baseline = baseline_dir / "assets-liabilities-overview.duckdb"
    active_database = tmp_path / "developer.duckdb"
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / ".dojo-e2e-worker").write_text("acceptance-secret", encoding="utf-8")
    build_baseline(E2EScenario.ASSETS_LIABILITIES_OVERVIEW, baseline)
    shutil.copyfile(baseline, active_database)

    app = create_app(
        Settings(
            APP_ENV="e2e",
            DUCKDB_PATH=str(active_database),
            E2E_BASELINE_DIR=str(baseline_dir),
            E2E_RUN_DIR=str(run_dir),
            E2E_RESET_TOKEN="acceptance-secret",
        )
    )

    with TestClient(app) as client:
        response = client.post(
            "/__e2e/reset",
            headers={"X-Dojo-E2E-Token": "acceptance-secret"},
            json={"scenario": E2EScenario.ASSETS_LIABILITIES_OVERVIEW.value},
        )

    assert response.status_code == 409
    assert response.json()["detail"] == "Unsafe E2E worker database configuration"
