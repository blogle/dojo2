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
	cd api && uv run python -m uvicorn dojo.api.main:app --reload --host 0.0.0.0 --port 8000

web:
	@printf '==> starting web dev server\n'
	cd web && pnpm dev --host 0.0.0.0 --port 5173

airship:
	@set -euo pipefail; \
	cd web; \
	args=(--host 0.0.0.0 --target 5173 --port 5174 --agent opencode --opencode-url http://127.0.0.1:4096 --safe); \
	if [[ -n "$${DOJO_AIRSHIP_ALLOWED_HOSTS:-}" ]]; then \
		read -r -a allowed_hosts <<< "$${DOJO_AIRSHIP_ALLOWED_HOSTS}"; \
		for host in "$${allowed_hosts[@]}"; do args+=(--allowed-hosts "$$host"); done; \
	fi; \
	DOJO_AIRSHIP_STATE_DIR="$$PWD/../.airship-state" dojo-airship "$${args[@]}"

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
	cd api && uv run python -m pytest tests/test_money.py tests/test_settings.py tests/test_importer.py tests/test_loan_projection.py tests/test_operations.py tests/test_backup.py tests/test_backup_access.py tests/test_backup_trigger.py tests/test_snapshot_backup.py tests/test_release.py tests/test_backup_credentials.py tests/test_drive_backup.py tests/test_drive_uploader.py tests/test_google.py

test-release:
	@printf '==> running release automation tests\n'
	cd api && uv run python -m pytest tests/test_release.py

test-property:
	@printf '==> running backend property tests\n'
	cd api && uv run python -m pytest tests/test_properties.py

test-integration:
	@printf '==> running backend integration tests\n'
	cd api && uv run python -m pytest tests/test_health.py tests/test_api_endpoints.py tests/test_backup_access.py tests/test_budget_formulas.py tests/test_account_values.py tests/test_reconciliation.py tests/test_scd.py tests/test_migrations.py tests/test_e2e.py

test-e2e:
	web/scripts/run-e2e.sh

test-e2e-spec spec:
	web/scripts/run-e2e.sh "{{spec}}"

record-flows:
	web/scripts/run-e2e.sh --record

record-flow flow:
	web/scripts/run-e2e.sh --record "{{flow}}"

storyboard:
	@set -euo pipefail; \
	output_dir="storyboards"; \
	log="$(mktemp)"; \
	trap 'rm -f "$log"' EXIT; \
	web/scripts/run-e2e.sh --record | tee "$log"; \
	recording_dir="$(while IFS= read -r line; do case "$line" in "Recording directory: "*) printf '%s\n' "${line#Recording directory: }";; esac; done < "$log")"; \
	test -n "$recording_dir"; \
	mkdir -p "$output_dir"; \
	count=0; \
	for source in "$recording_dir"/*.storyboard.png; do \
		if [[ ! -f "$source" ]]; then continue; fi; \
		cp "$source" "$output_dir/"; \
		count=$((count + 1)); \
	done; \
	test "$count" -eq 6; \
	printf 'Generated %s storyboard files in %s\n' "$count" "$output_dir"

profile-e2e:
	web/scripts/profile-e2e.sh

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
	cd api && uv run python -m mypy src
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

release-directive:
	python3 scripts/release.py directive

release-next-version bump="patch":
	python3 scripts/release.py next-version "{{bump}}"

docs-serve:
	cd docs && mdbook serve

validate-aggregates-fixture:
	cd api && uv run python -m dojo.validation_cli --fixture

validate-reviewed-aggregates-fixture:
	cd api && uv run python -m dojo.validation_cli --fixture --reviewed

validate-aggregates-dump dump:
	cd api && uv run python -m dojo.validation_cli --fetch-dump {{dump}}

validate-reviewed-aggregates-dump dump:
	cd api && uv run python -m dojo.validation_cli --fetch-dump {{dump}} --reviewed

backup-prepare source destination image_digest source_snapshot:
	cd api && uv run python -m dojo.backup prepare "{{source}}" "{{destination}}" --image-digest "{{image_digest}}" --source-snapshot "{{source_snapshot}}"

backup-verify database manifest:
	cd api && uv run python -m dojo.backup verify "{{database}}" "{{manifest}}"

backup-restore database manifest target:
	cd api && uv run python -m dojo.backup restore "{{database}}" "{{manifest}}" "{{target}}"

k8s-snapshot-backup:
	ops/k8s/snapshot-backup.sh

k8s-render: k8s-validate-backup-manifests
	kubectl kustomize deploy/k8s/base

k8s-validate-backup-manifests:
	ops/k8s/validate-backup-manifests.sh

drive-infra-fmt:
	tofu -chdir=infra/opentofu/google-backup fmt

drive-infra-fmt-check:
	tofu -chdir=infra/opentofu/google-backup fmt -check

drive-infra-init:
	tofu -chdir=infra/opentofu/google-backup init

drive-infra-validate:
	tofu -chdir=infra/opentofu/google-backup init -backend=false && tofu -chdir=infra/opentofu/google-backup validate

drive-infra-plan:
	tofu -chdir=infra/opentofu/google-backup plan

drive-infra-apply:
	tofu -chdir=infra/opentofu/google-backup apply

drive-rehearsal:
	ops/drive/rehearse.sh

drive-break-glass-rehearsal:
	ops/drive/rehearse-break-glass.sh

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

check: format-check lint typecheck architecture-check migration-check k8s-render test-unit test-property test-integration test-web build docs

ci: check test-e2e container

container:
	env -u LD_LIBRARY_PATH DOJO_BUILD_SHA="$(git rev-parse HEAD)" nix build .#container --impure

container-validate-provenance build_sha:
	env -u LD_LIBRARY_PATH DOJO_BUILD_SHA="{{build_sha}}" nix build .#container --impure
	ops/container/validate-build-metadata.sh "$(readlink -f result)" "{{build_sha}}"
