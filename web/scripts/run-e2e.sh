#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
cache_root="${XDG_CACHE_HOME:-$HOME/.cache}/dojo/e2e"
baseline_dir="${cache_root}/baselines"
run_id=$(date -u +%Y%m%dT%H%M%S)-$$
run_dir="${cache_root}/runs/${run_id}"
active_database="${run_dir}/worker.duckdb"
scenarios=(
  "assets-liabilities-overview"
  "tangible-asset-creation"
  "tracking-snapshot-correction"
  "cash-only-investment"
)
initial_baseline="${baseline_dir}/${scenarios[0]}.duckdb"
allocate_port() {
  node -e 'const server=require("node:net").createServer(); server.listen(0,"127.0.0.1",()=>{console.log(server.address().port);server.close();});'
}

api_port="${DOJO_E2E_API_PORT:-$(allocate_port)}"
web_port="${DOJO_E2E_WEB_PORT:-$(allocate_port)}"
api_url="http://127.0.0.1:${api_port}"
web_url="http://127.0.0.1:${web_port}"
reset_token="dojo-e2e-local-token"
browser="${DOJO_E2E_BROWSER:-chrome}"
spec="${1:-}"
spec="${spec#web/}"

mkdir -p "$baseline_dir" "$run_dir/cypress"
printf '%s' "$reset_token" >"$run_dir/.dojo-e2e-worker"

api_pid=""
web_pid=""

cleanup() {
  status=$?
  if [[ -n "$web_pid" ]]; then
    kill "$web_pid" 2>/dev/null || true
    wait "$web_pid" 2>/dev/null || true
  fi
  if [[ -n "$api_pid" ]]; then
    kill "$api_pid" 2>/dev/null || true
    wait "$api_pid" 2>/dev/null || true
  fi
  if [[ "$status" -eq 0 ]]; then
    rm -f "$active_database"
  else
    printf 'E2E failure artifacts retained at %s\n' "$run_dir" >&2
  fi
  exit "$status"
}
trap cleanup EXIT INT TERM

wait_for_url() {
  url=$1
  label=$2
  deadline=$((SECONDS + 30))
  until node -e 'fetch(process.argv[1]).then((response) => process.exit(response.ok ? 0 : 1)).catch(() => process.exit(1))' "$url"; do
    if (( SECONDS >= deadline )); then
      printf 'Timed out waiting for %s at %s\n' "$label" "$url" >&2
      return 1
    fi
    sleep 0.1
  done
}

baseline_started=$(date +%s%N)
baseline_bytes=0
for scenario in "${scenarios[@]}"; do
  baseline="${baseline_dir}/${scenario}.duckdb"
  (
    cd "$repo_root/api"
    uv run python -m dojo.e2e "$scenario" "$baseline"
  ) >"$run_dir/baseline-${scenario}.json"
  baseline_bytes=$((baseline_bytes + $(stat -c %s "$baseline")))
done
baseline_ms=$(( ($(date +%s%N) - baseline_started) / 1000000 ))
cp "$initial_baseline" "$active_database"

api_started=$(date +%s%N)
(
  cd "$repo_root/api"
  APP_ENV=e2e \
    DUCKDB_PATH="$active_database" \
    E2E_BASELINE_DIR="$baseline_dir" \
    E2E_RUN_DIR="$run_dir" \
    E2E_RESET_TOKEN="$reset_token" \
    SESSION_SECRET="dojo-e2e-session" \
    CORS_ALLOWED_ORIGINS="$web_url" \
    exec .venv/bin/python -m uvicorn dojo.api.main:app --host 127.0.0.1 --port "$api_port"
) >"$run_dir/api.log" 2>&1 &
api_pid=$!
wait_for_url "$api_url/health" "FastAPI"
api_startup_ms=$(( ($(date +%s%N) - api_started) / 1000000 ))

web_started=$(date +%s%N)
set +e
(
  cd "$repo_root/web"
  VITE_API_BASE_URL="$api_url" exec ./node_modules/.bin/vite --host 127.0.0.1 --port "$web_port" --strictPort
) >"$run_dir/web.log" 2>&1 &
web_pid=$!
wait_for_url "$web_url" "Vite"
web_startup_ms=$(( ($(date +%s%N) - web_started) / 1000000 ))

node - "$run_dir/harness.json" "$baseline_ms" "$api_startup_ms" "$web_startup_ms" "$baseline_bytes" <<'NODE'
import { writeFileSync } from "node:fs";

const [output, baselineMs, apiMs, webMs, baselineBytes] = process.argv.slice(2);
writeFileSync(
  output,
  JSON.stringify(
    {
      baselineGenerationMs: Number(baselineMs),
      apiStartupMs: Number(apiMs),
      webStartupMs: Number(webMs),
      baselineBytes: Number(baselineBytes),
    },
    null,
    2,
  ),
);
NODE

cypress_args=(run --e2e --browser "$browser")
if [[ -n "$spec" ]]; then
  cypress_args+=(--spec "$spec")
fi

(
  cd "$repo_root/web"
  CYPRESS_BASE_URL="$web_url" \
    VITE_API_BASE_URL="$api_url" \
    DOJO_E2E_TOKEN="$reset_token" \
    E2E_OUTPUT_DIR="$run_dir/cypress" \
    ./scripts/run-cypress.sh "${cypress_args[@]}"
)
cypress_status=$?
set -e

if [[ -f "$run_dir/cypress/run.json" ]]; then
  node "$repo_root/web/scripts/summarize-e2e.mjs" "$run_dir"
fi
if [[ -n "${DOJO_E2E_PROFILE_MANIFEST:-}" ]]; then
  printf '%s\n' "$run_dir" >>"$DOJO_E2E_PROFILE_MANIFEST"
fi
exit "$cypress_status"
