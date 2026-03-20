#!/usr/bin/env bash
set -euo pipefail

exec "$(dirname "$0")/run_agent_entrypoint.sh" default run-suite "$@"
