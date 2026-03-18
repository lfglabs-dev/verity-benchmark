#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

mkdir -p results

mapfile -t case_ids < <(python3 - <<'PY'
from pathlib import Path
from scripts.manifest_utils import load_manifest_data

for manifest in sorted(Path("cases").glob("*/*/case.yaml")):
    data = load_manifest_data(manifest)
    print(f"{data['project']}/{data['case_id']}")
PY
)

overall_status=0
for case_id in "${case_ids[@]}"; do
  ./scripts/run_case.sh "$case_id" || overall_status=$?
done

python3 - "${case_ids[@]}" <<'PY'
import json
from collections import Counter
from pathlib import Path
import sys

case_ids = sys.argv[1:]
result_files = [Path("results") / f"{case_id.replace('/', '__')}.json" for case_id in case_ids]
results = [json.loads(path.read_text(encoding="utf-8")) for path in result_files if path.exists()]
summary = {
  "total_cases": len(results),
  "status_counts": dict(sorted(Counter(item["status"] for item in results).items())),
  "cases": [item["case_id"] for item in results],
}
Path("results/summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
PY

exit "$overall_status"
