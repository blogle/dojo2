set shell := ["bash", "-cu"]

setup:
	@printf '==> syncing api dependencies\n'
	cd api && uv sync
	@printf '==> installing web dependencies\n'
	cd web && pnpm install

dev:
	@printf 'Run `just api` and `just web` in separate shells.\n'

api:
	@printf '==> provisioning api database\n'
	cd api && uv run python -m dojo.migrations "${DUCKDB_PATH:-.local/dojo.duckdb}"
	@printf '==> starting api server\n'
	cd api && uv run uvicorn dojo.api.main:app --reload --host 0.0.0.0 --port 8000

web:
	@printf '==> starting web dev server\n'
	cd web && pnpm dev --host 0.0.0.0 --port 5173

dev-api:
	just api

dev-web:
	just web

build: build-api build-web

build-api:
	cd api && uv build

build-web:
	cd web && pnpm build

test: test-unit test-property test-integration test-web

test-api:
	@printf '==> running backend tests\n'
	cd api && uv run pytest

test-web:
	@printf '==> running web tests\n'
	cd web && pnpm test

test-unit:
	@printf '==> running backend unit tests\n'
	cd api && uv run python -m pytest tests/test_money.py tests/test_settings.py tests/test_importer.py

test-property:
	@printf '==> running backend property tests\n'
	cd api && uv run python -m pytest tests/test_properties.py

test-integration:
	@printf '==> running backend integration tests\n'
	cd api && uv run python -m pytest tests/test_health.py tests/test_api_endpoints.py tests/test_budget_formulas.py tests/test_scd.py tests/test_migrations.py

test-e2e:
	@printf 'No Cypress suite is configured yet; deterministic browser e2e coverage remains a known gap in this repository.\n'

lint: lint-api lint-web

lint-api:
	@printf '==> linting api\n'
	cd api && uv run python -m ruff check .

lint-web:
	@printf '==> linting web\n'
	cd web && pnpm lint

format:
	@printf '==> formatting api\n'
	cd api && uv run python -m ruff format . && uv run python -m ruff check --fix .
	@printf '==> formatting web\n'
	cd web && pnpm format

format-check:
	@printf '==> checking api formatting\n'
	cd api && uv run python -m ruff format --check . && uv run python -m ruff check .
	@printf '==> checking web formatting\n'
	cd web && pnpm format:check

typecheck:
	@printf '==> type checking api\n'
	cd api && uv run mypy src
	@printf '==> type checking web\n'
	cd web && pnpm typecheck

architecture-check:
	@printf '==> running repository architecture and policy checks\n'
	cd api && uv run python -m pytest tests/architecture

migration-check:
	@printf '==> verifying fresh database provisioning\n'
	cd api && uv run python -m pytest tests/test_migrations.py

docs:
	@printf '==> building docs\n'
	cd docs && mdbook build

docs-serve:
	cd docs && mdbook serve

validate-aggregates-fixture:
	cd api && uv run python -m dojo.validation_cli --fixture

validate-aggregates-dump dump:
	cd api && uv run python -m dojo.validation_cli --fetch-dump {{dump}}

# --- Benchmarks ---

bench: bench-api bench-web

bench-api:
	cd api && uv run python -m pytest tests/test_benchmarks.py -v --tb=short -s -k "not test_full_backend_benchmark_suite"

bench-api-quick:
	cd api && uv run python -m pytest tests/test_benchmarks.py::TestBackendBenchmarks -v --tb=short -s -k "not test_full_backend_benchmark"

bench-api-routes:
	cd api && uv run python -m pytest tests/test_benchmarks.py::TestApiBenchmarks -v --tb=short -s

bench-api-report:
	cd api && uv run python -m dojo.benchmarks

bench-web:
	cd web && pnpm vitest run tests/ --reporter=verbose

clean:
	rm -rf api/dist api/build web/dist docs/book .pytest_cache .mypy_cache .ruff_cache

check: format-check lint typecheck architecture-check migration-check test-unit test-property test-integration test-web build docs

ci: check test-e2e container

container:
	env -u LD_LIBRARY_PATH nix build .#container
