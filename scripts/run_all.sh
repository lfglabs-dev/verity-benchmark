#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

mkdir -p results

mapfile -t task_refs < <(python3 harness/task_runner.py list --suite active)

overall_status=0
for task_ref in "${task_refs[@]}"; do
  ./scripts/run_task.sh "$task_ref" || overall_status=$?
done

python3 harness/task_runner.py aggregate --suite active "${task_refs[@]}"

exit "$overall_status"
