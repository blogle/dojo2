set shell := ["bash", "-cu"]

setup:
	cd api && uv sync
	cd web && pnpm install

dev:
	@printf 'Run `just dev-api` and `just dev-web` in separate shells.\n'

dev-api:
	cd api && uv run uvicorn dojo.api.main:app --reload --host 0.0.0.0 --port 8000

dev-web:
	cd web && pnpm dev --host 0.0.0.0 --port 5173

build: build-api build-web

build-api:
	cd api && uv build

build-web:
	cd web && pnpm build

test: test-api test-web

test-api:
	cd api && uv run pytest

test-web:
	cd web && pnpm test

lint: lint-api lint-web

lint-api:
	cd api && uv run python -m ruff check .

lint-web:
	cd web && pnpm lint

format:
	cd api && uv run python -m ruff format . && uv run python -m ruff check --fix .
	cd web && pnpm format

format-check:
	cd api && uv run python -m ruff format --check . && uv run python -m ruff check .
	cd web && pnpm format:check

typecheck:
	cd api && uv run mypy src
	cd web && pnpm typecheck

docs:
	cd docs && mdbook build

docs-serve:
	cd docs && mdbook serve

clean:
	rm -rf api/dist api/build web/dist docs/book .pytest_cache .mypy_cache .ruff_cache

container:
	env -u LD_LIBRARY_PATH nix build .#container
