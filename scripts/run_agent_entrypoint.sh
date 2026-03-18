#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

usage() {
  echo "usage: scripts/run_agent_entrypoint.sh <default|custom> <run|run-case|run-suite> [args...]" >&2
}

if [[ $# -lt 2 ]]; then
  usage
  exit 1
fi

profile_kind="$1"
shift
runner_command="$1"
shift

case "$profile_kind" in
  default)
    profile_field="default_agent_default_profile"
    ;;
  custom)
    profile_field="custom_agent_default_profile"
    ;;
  *)
    usage
    exit 1
    ;;
esac

case "$runner_command" in
  run)
    runner_args=()
    ;;
  run-case)
    runner_args=()
    ;;
  run-suite)
    runner_args=(--suite active)
    ;;
  *)
    usage
    exit 1
    ;;
esac

default_profile="$(python3 -c 'import sys; from pathlib import Path; sys.path.insert(0, str(Path.cwd() / "harness")); from benchmark_config import load_benchmark_agent_defaults; print(getattr(load_benchmark_agent_defaults(), sys.argv[1]))' "$profile_field")"

if [[ -n "${VERITY_BENCHMARK_AGENT_PROFILE:-}" && -n "${VERITY_BENCHMARK_AGENT_CONFIG:-}" ]]; then
  echo "set either VERITY_BENCHMARK_AGENT_PROFILE or VERITY_BENCHMARK_AGENT_CONFIG, not both" >&2
  exit 1
fi

if [[ -n "${VERITY_BENCHMARK_AGENT_PROFILE:-}" ]]; then
  exec python3 harness/agent_runner.py "$runner_command" "${runner_args[@]}" "$@" --profile "$VERITY_BENCHMARK_AGENT_PROFILE"
fi

if [[ -n "${VERITY_BENCHMARK_AGENT_CONFIG:-}" ]]; then
  exec python3 harness/agent_runner.py "$runner_command" "${runner_args[@]}" "$@" --config "$VERITY_BENCHMARK_AGENT_CONFIG"
fi

exec python3 harness/agent_runner.py "$runner_command" "${runner_args[@]}" "$@" --profile "$default_profile"
