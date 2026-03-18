#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

default_profile="$(python3 -c 'import sys; from pathlib import Path; sys.path.insert(0, str(Path.cwd() / "harness")); from benchmark_config import load_benchmark_agent_defaults; print(load_benchmark_agent_defaults().custom_agent_default_profile)')"

if [[ -n "${VERITY_BENCHMARK_AGENT_PROFILE:-}" && -n "${VERITY_BENCHMARK_AGENT_CONFIG:-}" ]]; then
  echo "set either VERITY_BENCHMARK_AGENT_PROFILE or VERITY_BENCHMARK_AGENT_CONFIG, not both" >&2
  exit 1
fi

if [[ -n "${VERITY_BENCHMARK_AGENT_PROFILE:-}" ]]; then
  python3 harness/agent_runner.py run-case "$@" --profile "$VERITY_BENCHMARK_AGENT_PROFILE"
elif [[ -n "${VERITY_BENCHMARK_AGENT_CONFIG:-}" ]]; then
  python3 harness/agent_runner.py run-case "$@" --config "$VERITY_BENCHMARK_AGENT_CONFIG"
else
  python3 harness/agent_runner.py run-case "$@" --profile "$default_profile"
fi
