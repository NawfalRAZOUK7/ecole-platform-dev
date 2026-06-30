#!/bin/sh
set -e

if [ "$(id -u)" = "0" ]; then
  vite_temp_dir="/app/node_modules/.vite-temp"
  mkdir -p "$vite_temp_dir"

  node_owner="$(id -u node):$(id -g node)"
  node_modules_owner="$(stat -c '%u:%g' /app/node_modules 2>/dev/null || true)"
  vite_temp_owner="$(stat -c '%u:%g' "$vite_temp_dir" 2>/dev/null || true)"

  if [ "$node_modules_owner" != "$node_owner" ]; then
    chown -R node:node /app/node_modules
  elif [ "$vite_temp_owner" != "$node_owner" ]; then
    chown -R node:node "$vite_temp_dir"
  fi

  exec su-exec node "$@"
fi

exec "$@"
