#!/usr/bin/env bash
set -euo pipefail

: "${DOJO_CYPRESS_APP_DIR:?DOJO_CYPRESS_APP_DIR must be set}"

version=$(node -p 'require("./node_modules/cypress/package.json").version')

export XDG_CONFIG_HOME="/tmp/opencode/dojo-cypress-config"
export XDG_CACHE_HOME="/tmp/opencode/dojo-cypress-xdg-cache"
export CYPRESS_CACHE_FOLDER="/tmp/opencode/dojo-cypress-cache"

binary_dir="${CYPRESS_CACHE_FOLDER}/${version}/Cypress"
mkdir -p "$(dirname "$binary_dir")"
ln -sfn "$DOJO_CYPRESS_APP_DIR" "$binary_dir"

output_file=$(mktemp /tmp/opencode/dojo-cypress-output.XXXXXX)

set +e
./node_modules/.bin/cypress "$@" >"$output_file" 2>&1
status=$?
set -e

while IFS= read -r line; do
  case "$line" in
    "DevTools listening on ws://"*) continue ;;
    "(node:"*"ExperimentalWarning: \
\`--experimental-loader\` may be removed in the future; instead use \
\`register()\`:" ) continue ;;
    "--import 'data:text/javascript,"*) continue ;;
    "(Use \`node --trace-warnings ...\` to show where the warning was created)") continue ;;
    "(node:"*"[DEP0180] DeprecationWarning: fs.Stats constructor is deprecated.") continue ;;
    "(Use \`node --trace-deprecation ...\` to show where the warning was created)") continue ;;
    *"The CJS build of Vite's Node API is deprecated."*) continue ;;
    "Port "*" is in use, trying another one...") continue ;;
    "resize:  can't open terminal /dev/tty") continue ;;
  esac

  printf '%s\n' "$line"
done < "$output_file"

rm -f "$output_file"

exit "$status"
