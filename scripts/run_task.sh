#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ "$#" -ne 1 ]; then
  echo "usage: ./scripts/run_task.sh <project/case_id/task_id>" >&2
  exit 1
fi

python3 harness/task_runner.py run "$1"
