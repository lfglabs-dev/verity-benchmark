#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if ! command -v dotenvx >/dev/null 2>&1; then
  exec "$@"
fi

if [[ "${VERITY_BENCHMARK_DOTENVX_LOADED:-}" == "1" ]]; then
  exec "$@"
fi

if [[ "${VERITY_BENCHMARK_ALLOW_PROCESS_SECRET_OVERRIDES:-}" != "1" ]]; then
  for managed_var in \
    OPENROUTER_API_KEY \
    VERITY_BENCHMARK_AGENT_API_KEY \
    VERITY_BENCHMARK_AGENT_BASE_URL \
    VERITY_BENCHMARK_AGENT_MODEL
  do
    unset "$managed_var"
  done
fi

env_args=()

if [[ -f .env ]]; then
  if grep -q "encrypted:" .env; then
    if [[ -n "${DOTENV_PRIVATE_KEY:-}" || -f .env.keys ]]; then
      env_args+=(-f .env)
    fi
  else
    env_args+=(-f .env)
  fi
fi

if [[ -f .env.local ]]; then
  env_args+=(-f .env.local)
fi

if [[ "${#env_args[@]}" -eq 0 ]]; then
  exec "$@"
fi

export VERITY_BENCHMARK_DOTENVX_LOADED=1
exec dotenvx run "${env_args[@]}" -- "$@"
