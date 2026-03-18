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
FAMILIES_ROOT = ROOT / "families"
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
RUNNABLE_TRANSLATION_STATUSES = {"translated"}
RUNNABLE_SPEC_STATUSES = {"draft", "frozen", "partial", "complete"}
RUNNABLE_PROOF_STATUSES = {"partial", "complete"}


def normalize_notes(path: Path, value: object) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError(f"{path}: notes must be a string or null")
    return value.strip()


def normalize_optional_string(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, list):
        return None
    text = str(value).strip()
    return text or None


def normalize_string_list(path: Path, key: str, value: object) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{path}: {key} must be a list")
    return [str(item).strip() for item in value]


def derive_spec_target(compile_target: str | None) -> str | None:
    if compile_target and compile_target.endswith(".Compile"):
        return compile_target[: -len(".Compile")] + ".Specs"
    return None


def evaluation_ready(
    target_kind: str,
    case_entry: dict,
    evaluation_target: str | None,
    evaluation_declaration: str | None,
    translation_status: str | None,
    spec_status: str | None,
    proof_status: str | None,
) -> bool:
    if case_entry["stage"] not in BUILDABLE_STAGES:
        return False
    if target_kind == "translation":
        return bool(evaluation_target) and translation_status in RUNNABLE_TRANSLATION_STATUSES
    if target_kind == "spec":
        return bool(evaluation_target and evaluation_declaration) and spec_status in RUNNABLE_SPEC_STATUSES
    if target_kind == "proof":
        return bool(evaluation_target and evaluation_declaration) and proof_status in RUNNABLE_PROOF_STATUSES
    return False


def load_case_manifest(path: Path, suite: str) -> dict:
    data = load_manifest_data(path)
    required = {
        "project",
        "case_id",
        "schema_version",
        "stage",
        "selected_functions",
        "source_language",
        "verity_version",
        "lean_toolchain",
        "notes",
        "family_id",
        "implementation_id",
        "translation_status",
        "spec_status",
        "proof_status",
    }
    missing = sorted(required - data.keys())
    if missing:
        raise ValueError(f"{path}: missing required keys: {', '.join(missing)}")

    stage = data["stage"]
    if stage not in ALLOWED_STAGES:
        raise ValueError(f"{path}: unsupported stage {stage!r}")

    selected_functions = normalize_string_list(path, "selected_functions", data["selected_functions"])
    buildable = stage in BUILDABLE_STAGES and bool(normalize_optional_string(data.get("lean_target")))

    entry = {
        "case_id": f"{data['project']}/{data['case_id']}",
        "project": data["project"],
        "case_name": data["case_id"],
        "suite": suite,
        "schema_version": data["schema_version"],
        "manifest_path": str(path.relative_to(ROOT)),
        "split": data.get("split", suite),
        "family_id": data["family_id"],
        "implementation_id": data["implementation_id"],
        "stage": stage,
        "translation_status": data["translation_status"],
        "spec_status": data["spec_status"],
        "proof_status": data["proof_status"],
        "source_language": data["source_language"],
        "upstream_repo": data.get("upstream_repo"),
        "upstream_commit": data.get("upstream_commit"),
        "original_contract_path": data.get("original_contract_path"),
        "source_ref": normalize_optional_string(data.get("source_ref")),
        "selected_functions": selected_functions,
        "lean_target": normalize_optional_string(data.get("lean_target")),
        "failure_reason": normalize_optional_string(data.get("failure_reason")),
        "notes": normalize_notes(path, data.get("notes")),
        "buildable": buildable,
        "verity_commit": data["verity_version"],
        "lean_toolchain": data["lean_toolchain"],
        "abstraction_level": normalize_optional_string(data.get("abstraction_level")),
        "abstraction_tags": normalize_string_list(path, "abstraction_tags", data.get("abstraction_tags")),
        "abstraction_notes": normalize_notes(path, data.get("abstraction_notes")),
        "unsupported_feature_codes": normalize_string_list(
            path, "unsupported_feature_codes", data.get("unsupported_feature_codes")
        ),
        "spec_target": normalize_optional_string(data.get("spec_target")),
        "proof_target": normalize_optional_string(data.get("proof_target")),
    }
    return entry


def load_task_manifest(path: Path, suite: str) -> dict:
    data = load_manifest_data(path)
    case_dir = path.parent.parent
    case_entry = load_case_manifest(case_dir / "case.yaml", suite)
    project = case_dir.parent.name
    case_name = case_dir.name
    task_id = normalize_optional_string(data.get("task_id")) or path.stem
    spec_target = normalize_optional_string(data.get("spec_target")) or derive_spec_target(case_entry["lean_target"])
    proof_target = normalize_optional_string(data.get("proof_target"))
    statement_id = normalize_optional_string(data.get("statement_id"))
    translation_status = normalize_optional_string(data.get("translation_status")) or case_entry["translation_status"]
    spec_status = normalize_optional_string(data.get("spec_status")) or case_entry["spec_status"]
    proof_status = normalize_optional_string(data.get("proof_status")) or case_entry["proof_status"]
    evaluation_target_kind = normalize_optional_string(data.get("evaluation_target_kind")) or "translation"
    evaluation_target = normalize_optional_string(data.get("evaluation_target"))
    evaluation_declaration = normalize_optional_string(data.get("evaluation_declaration"))

    entry = {
        "task_ref": f"{project}/{case_name}/{task_id}",
        "task_id": task_id,
        "case_id": normalize_optional_string(data.get("case_id")) or f"{project}/{case_name}",
        "suite": suite,
        "schema_version": data.get("schema_version", 1),
        "manifest_path": str(path.relative_to(ROOT)),
        "split": data.get("split", suite),
        "family_id": data.get("family_id"),
        "implementation_id": data.get("implementation_id"),
        "source_ref": normalize_optional_string(data.get("source_ref")) or case_entry["source_ref"],
        "task_interface_version": data.get("task_interface_version", 1),
        "track": normalize_optional_string(data.get("track")) or "unspecified",
        "property_class": normalize_optional_string(data.get("property_class")) or "unspecified",
        "category": normalize_optional_string(data.get("category")) or "unspecified",
        "difficulty": normalize_optional_string(data.get("difficulty")) or "unspecified",
        "statement_id": statement_id,
        "translation_status": translation_status,
        "spec_status": spec_status,
        "proof_status": proof_status,
        "allowed_files": normalize_string_list(path, "allowed_files", data.get("allowed_files")),
        "abstraction_level": normalize_optional_string(data.get("abstraction_level")),
        "abstraction_notes": normalize_notes(path, data.get("abstraction_notes")),
        "unsupported_feature_codes": normalize_string_list(
            path, "unsupported_feature_codes", data.get("unsupported_feature_codes")
        ),
        "spec_target": spec_target,
        "proof_target": proof_target,
        "evaluation": {
            "engine": normalize_optional_string(data.get("evaluation_engine")) or "lean_build",
            "target_kind": evaluation_target_kind,
            "target": evaluation_target,
            "declaration": evaluation_declaration,
        },
        "readiness": {
            "translation": (
                "ready"
                if case_entry["lean_target"]
                and case_entry["stage"] in BUILDABLE_STAGES
                and translation_status in RUNNABLE_TRANSLATION_STATUSES
                else "blocked"
            ),
            "spec": "ready" if spec_target and statement_id and spec_status in RUNNABLE_SPEC_STATUSES else "planned",
            "proof": "ready" if proof_target and statement_id and proof_status in RUNNABLE_PROOF_STATUSES else "planned",
            "evaluation": (
                "ready"
                if evaluation_ready(
                    evaluation_target_kind,
                    case_entry,
                    evaluation_target,
                    evaluation_declaration,
                    translation_status,
                    spec_status,
                    proof_status,
                )
                else "blocked"
            ),
        },
    }
    return entry


def load_manifest_group(root: Path, pattern: str, loader) -> list[dict]:
    if not root.exists():
        return []
    return [loader(path) for path in sorted(root.glob(pattern))]


def load_family_manifest(path: Path) -> dict:
    data = load_manifest_data(path)
    return {
        "family_id": data["family_id"],
        "display_name": data["display_name"],
        "split": data["split"],
        "status": data["status"],
        "description": normalize_notes(path, data.get("description")),
        "implementation_ids": normalize_string_list(path, "implementation_ids", data.get("implementation_ids")),
        "case_ids": normalize_string_list(path, "case_ids", data.get("case_ids")),
        "source_languages": normalize_string_list(path, "source_languages", data.get("source_languages")),
        "manifest_path": str(path.relative_to(ROOT)),
    }


def load_implementation_manifest(path: Path) -> dict:
    data = load_manifest_data(path)
    return {
        "family_id": data["family_id"],
        "implementation_id": data["implementation_id"],
        "display_name": data["display_name"],
        "split": data["split"],
        "status": data["status"],
        "upstream_repo": data.get("upstream_repo"),
        "upstream_commit": data.get("upstream_commit"),
        "source_language": data["source_language"],
        "source_artifact_path": data["source_artifact_path"],
        "case_ids": normalize_string_list(path, "case_ids", data.get("case_ids")),
        "notes": normalize_notes(path, data.get("notes")),
        "manifest_path": str(path.relative_to(ROOT)),
    }


def render_case(entry: dict) -> list[str]:
    lines = [
        f"### `{entry['case_id']}`",
        f"- Family / implementation: `{entry['family_id']}` / `{entry['implementation_id']}`",
        f"- Stage: `{entry['stage']}`",
        (
            "- Status dimensions:"
            f" translation=`{entry['translation_status']}`"
            f", spec=`{entry['spec_status']}`"
            f", proof=`{entry['proof_status']}`"
        ),
    ]
    if entry["lean_target"]:
        lines.append(f"- Lean target: `{entry['lean_target']}`")
    if entry["failure_reason"]:
        lines.append(f"- Failure reason: `{entry['failure_reason']}`")
    if entry["source_ref"]:
        lines.append(f"- Source ref: `{entry['source_ref']}`")
    if entry["selected_functions"]:
        joined = ", ".join(f"`{name}`" for name in entry["selected_functions"])
        lines.append(f"- Selected functions: {joined}")
    if entry["original_contract_path"]:
        lines.append(f"- Source artifact: `{entry['original_contract_path']}`")
    lines.append(f"- Notes: {entry['notes']}")
    return lines


def render_task(entry: dict) -> list[str]:
    lines = [
        f"### `{entry['task_ref']}`",
        f"- Track / property class: `{entry['track']}` / `{entry['property_class']}`",
        (
            "- Readiness:"
            f" translation=`{entry['readiness']['translation']}`"
            f", spec=`{entry['readiness']['spec']}`"
            f", proof=`{entry['readiness']['proof']}`"
            f", evaluation=`{entry['readiness']['evaluation']}`"
        ),
    ]
    if entry["statement_id"]:
        lines.append(f"- Statement id: `{entry['statement_id']}`")
    lines.append(
        "- Evaluation:"
        f" engine=`{entry['evaluation']['engine']}`"
        f", target_kind=`{entry['evaluation']['target_kind']}`"
        f", target=`{entry['evaluation']['target']}`"
        f", declaration=`{entry['evaluation']['declaration']}`"
    )
    if entry["spec_target"]:
        lines.append(f"- Spec target: `{entry['spec_target']}`")
    if entry["proof_target"]:
        lines.append(f"- Proof target: `{entry['proof_target']}`")
    return lines


def summary_counts(entries: list[dict], field: str) -> dict[str, int]:
    return dict(sorted(Counter(str(entry[field]) for entry in entries).items()))


def write_inventory(
    active_cases: list[dict],
    backlog_cases: list[dict],
    active_tasks: list[dict],
    backlog_tasks: list[dict],
    families: list[dict],
    implementations: list[dict],
) -> None:
    all_cases = active_cases + backlog_cases
    all_tasks = active_tasks + backlog_tasks
    payload = {
        "benchmark": "verity-benchmark",
        "manifest_schema_version": 1,
        "inventory_source": {
            "families": "families/*/family.yaml",
            "implementations": "families/*/implementations/*/implementation.yaml",
            "active_cases": "cases/*/*/case.yaml",
            "active_tasks": "cases/*/*/tasks/*.yaml",
            "backlog_cases": "backlog/*/*/case.yaml",
            "backlog_tasks": "backlog/*/*/tasks/*.yaml",
        },
        "summary": {
            "family_count": len(families),
            "implementation_count": len(implementations),
            "active_case_count": len(active_cases),
            "backlog_case_count": len(backlog_cases),
            "active_task_count": len(active_tasks),
            "backlog_task_count": len(backlog_tasks),
            "buildable_case_count": sum(1 for entry in active_cases if entry["buildable"]),
            "runnable_task_count": sum(
                1
                for entry in active_tasks
                if entry["readiness"]["evaluation"] == "ready"
            ),
            "case_stage_counts": summary_counts(all_cases, "stage"),
            "translation_status_counts": summary_counts(all_cases, "translation_status"),
            "spec_status_counts": summary_counts(all_cases, "spec_status"),
            "proof_status_counts": summary_counts(all_cases, "proof_status"),
            "task_track_counts": summary_counts(all_tasks, "track"),
            "task_property_class_counts": summary_counts(all_tasks, "property_class"),
            "family_split_counts": summary_counts(families, "split"),
        },
        "families": families,
        "implementations": implementations,
        "cases": active_cases,
        "backlog": backlog_cases,
        "tasks": active_tasks,
        "backlog_tasks": backlog_tasks,
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


def write_report(
    active_cases: list[dict],
    backlog_cases: list[dict],
    active_tasks: list[dict],
    families: list[dict],
    implementations: list[dict],
) -> None:
    buildable_cases = [entry for entry in active_cases if entry["buildable"]]
    blocked_cases = [entry for entry in active_cases if not entry["buildable"]]

    lines = [
        "# Benchmark report",
        "",
        "This report is generated from the benchmark manifests.",
        "",
        "## Summary",
        "",
        f"- Families: {len(families)}",
        f"- Implementations: {len(implementations)}",
        f"- Active cases: {len(active_cases)}",
        f"- Buildable active cases: {len(buildable_cases)}",
        f"- Active tasks: {len(active_tasks)}",
        f"- Backlog cases: {len(backlog_cases)}",
        "",
        "## Buildable active cases",
        "",
    ]

    if buildable_cases:
        for entry in buildable_cases:
            lines.extend(render_case(entry))
            lines.append("")
    else:
        lines.extend(["- None", ""])

    lines.extend(["## Non-buildable active cases", ""])
    if blocked_cases:
        for entry in blocked_cases:
            lines.extend(render_case(entry))
            lines.append("")
    else:
        lines.extend(["- None", ""])

    lines.extend(["## Active tasks", ""])
    if active_tasks:
        for entry in active_tasks:
            lines.extend(render_task(entry))
            lines.append("")
    else:
        lines.extend(["- None", ""])

    lines.extend(["## Backlog", ""])
    if backlog_cases:
        for entry in backlog_cases:
            lines.extend(render_case(entry))
            lines.append("")
    else:
        lines.extend(["- None", ""])

    lines.extend([
        "## Commands",
        "",
        "- Validate manifests: `python3 scripts/validate_manifests.py`",
        "- Regenerate metadata: `python3 scripts/generate_metadata.py`",
        "- Run one task: `./scripts/run_task.sh <project/case_id/task_id>`",
        "- Run one case: `./scripts/run_case.sh <project/case_id>`",
        "- Run active suite: `./scripts/run_all.sh`",
        "- Run repo check: `./scripts/check.sh`",
        "",
    ])
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    families = load_manifest_group(FAMILIES_ROOT, "*/family.yaml", load_family_manifest)
    implementations = load_manifest_group(
        FAMILIES_ROOT, "*/implementations/*/implementation.yaml", load_implementation_manifest
    )
    active_cases = load_manifest_group(ACTIVE_ROOT, "*/*/case.yaml", lambda path: load_case_manifest(path, "active"))
    backlog_cases = load_manifest_group(
        BACKLOG_ROOT, "*/*/case.yaml", lambda path: load_case_manifest(path, "backlog")
    )
    active_tasks = load_manifest_group(ACTIVE_ROOT, "*/*/tasks/*.yaml", lambda path: load_task_manifest(path, "active"))
    backlog_tasks = load_manifest_group(
        BACKLOG_ROOT, "*/*/tasks/*.yaml", lambda path: load_task_manifest(path, "backlog")
    )

    if not active_cases and not backlog_cases:
        print("no case manifests found", file=sys.stderr)
        return 1

    write_inventory(active_cases, backlog_cases, active_tasks, backlog_tasks, families, implementations)
    write_report(active_cases, backlog_cases, active_tasks, families, implementations)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
