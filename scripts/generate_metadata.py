#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import sys

from manifest_utils import load_manifest_data

ROOT = Path(__file__).resolve().parent.parent
ACTIVE_ROOT = ROOT / "cases"
BACKLOG_ROOT = ROOT / "backlog"
INVENTORY_PATH = ROOT / "benchmark-inventory.json"
REPORT_PATH = ROOT / "REPORT.md"

ALLOWED_STAGES = {
    "candidate",
    "scoped",
    "build_green",
    "proof_partial",
    "proof_complete",
}
BUILDABLE_STAGES = {"build_green", "proof_partial", "proof_complete"}
REQUIRED_KEYS = {
    "project",
    "case_id",
    "schema_version",
    "stage",
    "selected_functions",
    "source_language",
    "verity_version",
    "lean_toolchain",
    "notes",
}


def normalize_notes(path: Path, value: object) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError(f"{path}: notes must be a string or null")
    return value.strip()


def load_manifest(path: Path, suite: str) -> dict:
    data = load_manifest_data(path)

    missing = sorted(REQUIRED_KEYS - data.keys())
    if missing:
        raise ValueError(f"{path}: missing required keys: {', '.join(missing)}")

    stage = data["stage"]
    if stage not in ALLOWED_STAGES:
        raise ValueError(f"{path}: unsupported stage {stage!r}")

    if not isinstance(data["selected_functions"], list):
        raise ValueError(f"{path}: selected_functions must be a list")

    full_case_id = f"{data['project']}/{data['case_id']}"
    entry = {
        "case_id": full_case_id,
        "suite": suite,
        "schema_version": data["schema_version"],
        "stage": stage,
        "source_language": data["source_language"],
        "upstream_repo": data.get("upstream_repo"),
        "upstream_commit": data.get("upstream_commit"),
        "original_contract_path": data.get("original_contract_path"),
        "selected_functions": data["selected_functions"],
        "lean_target": data.get("lean_target"),
        "failure_reason": data.get("failure_reason"),
        "notes": normalize_notes(path, data.get("notes")),
        "manifest_path": str(path.relative_to(ROOT)),
        "buildable": stage in BUILDABLE_STAGES and bool(data.get("lean_target")),
        "verity_commit": data["verity_version"],
        "lean_toolchain": data["lean_toolchain"],
    }
    return entry


def collect_cases(root: Path, suite: str) -> list[dict]:
    if not root.exists():
        return []
    manifests = sorted(root.glob("*/*/case.yaml"))
    return [load_manifest(path, suite) for path in manifests]


def render_case(entry: dict) -> list[str]:
    lines = [f"### `{entry['case_id']}`", f"- Stage: `{entry['stage']}`"]
    if entry["lean_target"]:
        lines.append(f"- Lean target: `{entry['lean_target']}`")
    if entry["failure_reason"]:
        lines.append(f"- Failure reason: `{entry['failure_reason']}`")
    if entry["selected_functions"]:
        joined = ", ".join(f"`{name}`" for name in entry["selected_functions"])
        lines.append(f"- Selected functions: {joined}")
    if entry["original_contract_path"]:
        lines.append(f"- Source artifact: `{entry['original_contract_path']}`")
    lines.append(f"- Notes: {entry['notes']}")
    return lines


def write_inventory(active: list[dict], backlog: list[dict]) -> None:
    all_cases = active + backlog
    summary = {
        "active_cases": len(active),
        "backlog_cases": len(backlog),
        "buildable_cases": sum(1 for entry in active if entry["buildable"]),
        "stages": dict(sorted(Counter(entry["stage"] for entry in all_cases).items())),
    }

    payload = {
        "benchmark": "verity-benchmark",
        "manifest_schema_version": 1,
        "inventory_source": {
            "active": "cases/*/*/case.yaml",
            "backlog": "backlog/*/*/case.yaml",
        },
        "summary": summary,
        "cases": active,
        "backlog": backlog,
    }

    generated_at = datetime.now(timezone.utc).isoformat()
    if INVENTORY_PATH.exists():
        existing = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
        existing_without_timestamp = {
            key: value for key, value in existing.items() if key != "generated_at"
        }
        if existing_without_timestamp == payload:
            generated_at = str(existing.get("generated_at", generated_at))

    payload["generated_at"] = generated_at

    INVENTORY_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_report(active: list[dict], backlog: list[dict]) -> None:
    buildable = [entry for entry in active if entry["buildable"]]
    non_buildable = [entry for entry in active if not entry["buildable"]]

    lines = [
        "# Benchmark report",
        "",
        "This report is generated from the per-case `case.yaml` manifests.",
        "",
        "## Summary",
        "",
        f"- Active cases: {len(active)}",
        f"- Buildable active cases: {len(buildable)}",
        f"- Backlog entries: {len(backlog)}",
        "",
        "## Buildable active cases",
        "",
    ]

    if buildable:
        for entry in buildable:
            lines.extend(render_case(entry))
            lines.append("")
    else:
        lines.append("- None")
        lines.append("")

    lines.extend([
        "## Non-buildable active cases",
        "",
    ])

    if non_buildable:
        for entry in non_buildable:
            lines.extend(render_case(entry))
            lines.append("")
    else:
        lines.append("- None")
        lines.append("")

    lines.extend([
        "## Backlog",
        "",
    ])

    if backlog:
        for entry in backlog:
            lines.extend(render_case(entry))
            lines.append("")
    else:
        lines.append("- None")
        lines.append("")

    lines.extend([
        "## Commands",
        "",
        "- Regenerate metadata: `python3 scripts/generate_metadata.py`",
        "- Run one case: `./scripts/run_case.sh <project/case_id>`",
        "- Run active suite: `./scripts/run_all.sh`",
        "- Run repo check: `./scripts/check.sh`",
        "",
    ])

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    active = collect_cases(ACTIVE_ROOT, "active")
    backlog = collect_cases(BACKLOG_ROOT, "backlog")
    if not active and not backlog:
        print("no case manifests found", file=sys.stderr)
        return 1

    write_inventory(active, backlog)
    write_report(active, backlog)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
