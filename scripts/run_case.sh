#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ "$#" -ne 1 ]; then
  echo "usage: ./scripts/run_case.sh <project/case_id>" >&2
  exit 1
fi

case_ref="$1"
manifest=""
for root in cases backlog; do
  candidate="${root}/${case_ref}/case.yaml"
  if [ -f "$candidate" ]; then
    manifest="$candidate"
    break
  fi
done

if [ -z "$manifest" ]; then
  echo "case manifest not found for ${case_ref}" >&2
  exit 1
fi

mkdir -p results

tmp_json="$(mktemp)"
python3 - "$manifest" "$tmp_json" <<'PY'
import json
from pathlib import Path
import sys
from scripts.manifest_utils import load_manifest_data

manifest = Path(sys.argv[1])
out = Path(sys.argv[2])
data = load_manifest_data(manifest)
suite = "active" if manifest.parts[0] == "cases" else "backlog"
payload = {
    "case_id": f"{data['project']}/{data['case_id']}",
    "stage": data["stage"],
    "suite": suite,
    "lean_target": data.get("lean_target"),
    "lean_toolchain": data["lean_toolchain"],
    "verity_commit": data["verity_version"],
    "failure_reason": data.get("failure_reason"),
}
out.write_text(json.dumps(payload), encoding="utf-8")
PY

case_id="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["case_id"])' "$tmp_json")"
stage="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["stage"])' "$tmp_json")"
lean_target="$(python3 -c 'import json,sys; data=json.load(open(sys.argv[1])); print(data["lean_target"] or "")' "$tmp_json")"
failure_reason="$(python3 -c 'import json,sys; data=json.load(open(sys.argv[1])); print(data["failure_reason"] or "")' "$tmp_json")"

result_path="results/${case_id//\//__}.json"
start_epoch="$(date +%s)"
timestamp="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

if [ -n "$lean_target" ] && [[ "$stage" =~ ^(build_green|proof_partial|proof_complete)$ ]]; then
  set +e
  lake build "$lean_target"
  command_status=$?
  set -e

  if [ "$command_status" -eq 0 ]; then
    status="passed"
    reached_stage="$stage"
  else
    status="failed"
    reached_stage="build_failed"
    if [ -z "$failure_reason" ]; then
      failure_reason="build_error"
    fi
  fi
else
  status="not_runnable"
  reached_stage="$stage"
fi

end_epoch="$(date +%s)"
duration="$((end_epoch - start_epoch))"

python3 - "$tmp_json" "$result_path" "$status" "$reached_stage" "$failure_reason" "$duration" "$timestamp" <<'PY'
import json
from pathlib import Path
import sys

tmp_json = Path(sys.argv[1])
result_path = Path(sys.argv[2])
status = sys.argv[3]
reached_stage = sys.argv[4]
failure_reason = sys.argv[5] or None
duration = int(sys.argv[6])
timestamp = sys.argv[7]
payload = json.loads(tmp_json.read_text(encoding="utf-8"))
payload.update({
    "status": status,
    "reached_stage": reached_stage,
    "failure_reason": failure_reason,
    "duration_seconds": duration,
    "timestamp_utc": timestamp,
})
result_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(result_path)
PY

rm -f "$tmp_json"

if [ "$status" = "failed" ]; then
  exit 1
fi
