#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "results"
TASK_RESULTS_DIR = RESULTS_DIR / "tasks"

if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from manifest_utils import load_manifest_data

RUNNABLE_STAGES = {"build_green", "proof_partial", "proof_complete"}
PROOF_READY_STATUSES = {"partial", "complete"}
PLACEHOLDER_TOKENS = ("sorry", "admit", "axiom")


def normalize_optional_string(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, list):
        return None
    text = str(value).strip()
    return text or None


def normalize_list(value: object) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"expected list, got {type(value).__name__}")
    return [str(item).strip() for item in value if str(item).strip()]


def lean_module_name(rel_path: str) -> str:
    path = Path(rel_path)
    if path.suffix != ".lean":
        raise ValueError(f"expected Lean file path, got {rel_path!r}")
    return ".".join(path.with_suffix("").parts)


def editable_ready(task: dict[str, Any]) -> bool:
    return (
        task["stage"] in RUNNABLE_STAGES
        and task["translation_status"] == "translated"
        and task["proof_status"] in PROOF_READY_STATUSES
        and len(task["editable_files"]) == 1
        and bool(task["theorem_name"])
    )


def reference_solution_ready(task: dict[str, Any]) -> bool:
    reference = task["reference_solution"]
    return (
        task["stage"] in RUNNABLE_STAGES
        and task["translation_status"] == "translated"
        and task["proof_status"] in PROOF_READY_STATUSES
        and bool(reference["module"] and reference["declaration"])
    )


def task_ref_from_manifest(task_manifest: Path) -> str:
    case_dir = task_manifest.parent.parent
    return f"{case_dir.parent.name}/{case_dir.name}/{task_manifest.stem}"


def resolve_task_manifest(task_ref: str) -> Path:
    parts = task_ref.split("/")
    if len(parts) != 3:
        raise SystemExit("usage: <project/case_id/task_id>")

    project, case_name, task_id = parts
    candidates = [
        ROOT / "cases" / project / case_name / "tasks" / f"{task_id}.yaml",
        ROOT / "backlog" / project / case_name / "tasks" / f"{task_id}.yaml",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise SystemExit(f"task manifest not found for {task_ref}")


def discover_task_refs(suite_filter: str = "active") -> list[str]:
    refs: list[str] = []
    seen_paths: dict[str, Path] = {}
    if suite_filter == "all":
        roots = [ROOT / "cases", ROOT / "backlog"]
    elif suite_filter == "backlog":
        roots = [ROOT / "backlog"]
    else:
        roots = [ROOT / "cases"]

    for root in roots:
        if not root.exists():
            continue
        for task_manifest in sorted(root.glob("*/*/tasks/*.yaml")):
            task_ref = task_ref_from_manifest(task_manifest)
            previous = seen_paths.get(task_ref)
            if previous is not None:
                raise SystemExit(
                    "duplicate task ref discovered across suites: "
                    f"{task_ref} ({previous.relative_to(ROOT)} and {task_manifest.relative_to(ROOT)})"
                )
            seen_paths[task_ref] = task_manifest
            refs.append(task_ref)
    return refs


def load_case_record(case_manifest: Path) -> dict[str, Any]:
    data = load_manifest_data(case_manifest)
    suite = "active" if case_manifest.parts[-4] == "cases" else "backlog"
    return {
        "case_id": f"{data['project']}/{data['case_id']}",
        "suite": suite,
        "stage": data["stage"],
        "lean_target": normalize_optional_string(data.get("lean_target")),
        "failure_reason": normalize_optional_string(data.get("failure_reason")),
        "translation_status": normalize_optional_string(data.get("translation_status")) or "not_started",
        "spec_status": normalize_optional_string(data.get("spec_status")) or "not_started",
        "proof_status": normalize_optional_string(data.get("proof_status")) or "not_started",
        "manifest_path": str(case_manifest.relative_to(ROOT)),
    }


def load_task_record(task_manifest: Path) -> dict[str, Any]:
    task_data = load_manifest_data(task_manifest)
    case_manifest = task_manifest.parent.parent / "case.yaml"
    case_data = load_case_record(case_manifest)

    task_id = normalize_optional_string(task_data.get("task_id")) or task_manifest.stem
    task_ref = f"{case_data['case_id']}/{task_id}"
    translation_status = normalize_optional_string(task_data.get("translation_status")) or case_data["translation_status"]
    proof_status = normalize_optional_string(task_data.get("proof_status")) or case_data["proof_status"]
    editable_files = normalize_list(task_data.get("editable_files"))

    task = {
        "benchmark": "verity-benchmark",
        "schema_version": 1,
        "task_ref": task_ref,
        "task_id": task_id,
        "case_id": case_data["case_id"],
        "suite": case_data["suite"],
        "stage": case_data["stage"],
        "track": normalize_optional_string(task_data.get("track")) or "unspecified",
        "property_class": normalize_optional_string(task_data.get("property_class")) or "unspecified",
        "category": normalize_optional_string(task_data.get("category")) or "unspecified",
        "difficulty": normalize_optional_string(task_data.get("difficulty")) or "unspecified",
        "theorem_name": normalize_optional_string(task_data.get("theorem_name")),
        "proof_family": normalize_optional_string(task_data.get("proof_family")) or "unspecified",
        "source_ref": normalize_optional_string(task_data.get("source_ref")) or None,
        "task_interface_version": int(task_data.get("task_interface_version", 1)),
        "implementation_files": normalize_list(task_data.get("implementation_files")),
        "specification_files": normalize_list(task_data.get("specification_files")),
        "editable_files": editable_files,
        "translation_status": translation_status,
        "proof_status": proof_status,
        "failure_reason": case_data["failure_reason"],
        "manifest_path": str(task_manifest.relative_to(ROOT)),
        "case_manifest_path": case_data["manifest_path"],
        "targets": {
            "editable_file": editable_files[0] if len(editable_files) == 1 else None,
            "editable_module": (
                lean_module_name(editable_files[0]) if len(editable_files) == 1 else None
            ),
            "theorem_name": normalize_optional_string(task_data.get("theorem_name")),
        },
        "evaluation": {
            "engine": normalize_optional_string(task_data.get("evaluation_engine")) or "lean_proof_generation",
            "target_kind": "proof_generation",
        },
        "reference_solution": {
            "module": normalize_optional_string(task_data.get("reference_solution_module")),
            "declaration": normalize_optional_string(task_data.get("reference_solution_declaration"))
            or normalize_optional_string(task_data.get("theorem_name")),
        },
        "readiness": {},
    }
    task["readiness"] = {
        "prompt_context": "ready" if task["implementation_files"] and task["specification_files"] and editable_files else "blocked",
        "editable_proof": "ready" if editable_ready(task) else "blocked",
        "reference_solution": "ready" if reference_solution_ready(task) else "blocked",
    }
    return task


def run_command(command: list[str], *, cwd: Path = ROOT) -> tuple[int, str]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    output = (completed.stdout + completed.stderr).strip()
    return completed.returncode, output


def classify_lean_failure(output: str) -> str:
    if "external command 'git' exited with code 1" in output and "checking out revision" in output:
        return "dependency_checkout_failed"
    return "lean_check_failed"


def declaration_exists(module_name: str, declaration_name: str, *, cwd: Path = ROOT) -> tuple[bool, str]:
    with tempfile.TemporaryDirectory(prefix="verity-benchmark-check-") as tmp_dir:
        check_path = Path(tmp_dir) / "Check.lean"
        check_path.write_text(
            f"import {module_name}\n#check {declaration_name}\n",
            encoding="utf-8",
        )
        code, output = run_command(["lake", "env", "lean", str(check_path)], cwd=cwd)
        return code == 0, output


def execute_reference_solution_task(task_ref: str) -> tuple[int, Path]:
    task_manifest = resolve_task_manifest(task_ref)
    task = load_task_record(task_manifest)
    TASK_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    result_path = TASK_RESULTS_DIR / f"{task_ref.replace('/', '__')}.json"

    reference = task["reference_solution"]
    started_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    start = time.time()
    failure_mode: str | None = None
    execution_status = "not_runnable"
    execution_output = ""
    command: list[str] = []

    if task["evaluation"]["engine"] != "lean_proof_generation":
        failure_mode = "unsupported_evaluation_engine"
    elif task["readiness"]["reference_solution"] != "ready":
        failure_mode = task["failure_reason"] or "reference_solution_not_ready"
    else:
        command = ["lake", "build", reference["module"]]
        code, execution_output = run_command(command)
        if code == 0 and reference["declaration"]:
            exists, decl_output = declaration_exists(reference["module"], reference["declaration"])
            if exists:
                execution_status = "passed"
            else:
                execution_status = "failed"
                failure_mode = "reference_declaration_missing"
                execution_output = "\n".join(filter(None, [execution_output, decl_output]))
        else:
            execution_status = "passed" if code == 0 else "failed"
        if code != 0:
            failure_mode = classify_lean_failure(execution_output)

    completed_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    duration_seconds = round(time.time() - start, 3)

    payload = {
        "benchmark": task["benchmark"],
        "schema_version": task["schema_version"],
        "unit": "task",
        "run_id": f"{task_ref}:{started_at}",
        "task_ref": task["task_ref"],
        "task_id": task["task_id"],
        "case_id": task["case_id"],
        "suite": task["suite"],
        "track": task["track"],
        "property_class": task["property_class"],
        "category": task["category"],
        "difficulty": task["difficulty"],
        "theorem_name": task["theorem_name"],
        "proof_family": task["proof_family"],
        "source_ref": task["source_ref"],
        "task_interface_version": task["task_interface_version"],
        "command": command,
        "started_at": started_at,
        "completed_at": completed_at,
        "outcome": execution_status,
        "exit_code": 0 if execution_status == "passed" else 1,
        "status": execution_status,
        "failure_mode": failure_mode,
        "failure_reason": task["failure_reason"],
        "manifests": {
            "task": task["manifest_path"],
            "case": task["case_manifest_path"],
        },
        "artifacts": [str(result_path.relative_to(ROOT))],
        "metrics": {
            "duration_seconds": duration_seconds,
        },
        "environment": {
            "stage": task["stage"],
            "translation_status": task["translation_status"],
            "proof_status": task["proof_status"],
            "evaluation_engine": task["evaluation"]["engine"],
            "target_kind": task["evaluation"]["target_kind"],
        },
        "evaluation": task["evaluation"],
        "implementation_files": task["implementation_files"],
        "specification_files": task["specification_files"],
        "editable_files": task["editable_files"],
        "readiness": task["readiness"],
        "targets": task["targets"],
        "reference_solution": task["reference_solution"],
        "output": execution_output,
    }
    result_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return (0 if execution_status == "passed" else 1), result_path


def load_case_records_for_suite(suite: str) -> list[dict[str, Any]]:
    roots = []
    if suite in {"active", "all"}:
        roots.append(ROOT / "cases")
    if suite in {"backlog", "all"}:
        roots.append(ROOT / "backlog")

    records = []
    for root in roots:
        if not root.exists():
            continue
        for case_manifest in sorted(root.glob("*/*/case.yaml")):
            records.append(load_case_record(case_manifest))
    return records


def aggregate_results(task_refs: list[str], suite: str) -> dict[str, Any]:
    explicit_task_refs = bool(task_refs)
    if not task_refs:
        task_refs = discover_task_refs(suite)

    results = []
    selected_case_ids: set[str] = set()
    missing_task_refs: list[str] = []
    for task_ref in task_refs:
        task_manifest = resolve_task_manifest(task_ref)
        selected_case_ids.add(load_task_record(task_manifest)["case_id"])
        path = TASK_RESULTS_DIR / f"{task_ref.replace('/', '__')}.json"
        if path.exists():
            results.append(json.loads(path.read_text(encoding="utf-8")))
        else:
            missing_task_refs.append(task_ref)

    task_status_counts = Counter(item["status"] for item in results)
    if missing_task_refs:
        task_status_counts["missing"] = len(missing_task_refs)
    failure_mode_counts = Counter(item["failure_mode"] for item in results if item["failure_mode"])
    by_track: dict[str, Counter[str]] = defaultdict(Counter)
    by_property_class: dict[str, Counter[str]] = defaultdict(Counter)
    by_case: dict[str, list[dict[str, Any]]] = defaultdict(list)
    readiness_counts: dict[str, dict[str, int]] = {}
    proof_family_counts = Counter(item["proof_family"] for item in results)

    for item in results:
        by_track[item["track"]][item["status"]] += 1
        by_property_class[item["property_class"]][item["status"]] += 1
        by_case[item["case_id"]].append(item)

    for key in ("prompt_context", "editable_proof", "reference_solution"):
        readiness_counts[key] = dict(sorted(Counter(item["readiness"][key] for item in results).items()))

    case_rows = []
    all_case_records = load_case_records_for_suite(suite)
    if explicit_task_refs:
        case_records = [record for record in all_case_records if record["case_id"] in selected_case_ids]
    else:
        case_records = all_case_records
    for case_record in case_records:
        case_id = case_record["case_id"]
        case_results = by_case.get(case_id, [])
        statuses = [entry["status"] for entry in case_results]
        if statuses:
            if any(status == "failed" for status in statuses):
                case_status = "failed"
            elif any(status == "passed" for status in statuses):
                case_status = "passed"
            else:
                case_status = "not_runnable"
            case_status_counts = dict(sorted(Counter(statuses).items()))
        else:
            case_status = "not_runnable"
            case_status_counts = {}

        case_rows.append(
            {
                "case_id": case_id,
                "suite": case_record["suite"],
                "stage": case_record["stage"],
                "lean_target": case_record["lean_target"],
                "failure_reason": case_record["failure_reason"],
                "status": case_status,
                "task_count": len(case_results),
                "status_counts": case_status_counts,
            }
        )

    task_summary = {
        "benchmark": "verity-benchmark",
        "schema_version": 1,
        "unit": "task",
        "total_tasks": len(task_refs),
        "status_counts": dict(sorted(task_status_counts.items())),
        "failure_mode_counts": dict(sorted(failure_mode_counts.items())),
        "track_status_counts": {
            key: dict(sorted(value.items()))
            for key, value in sorted(by_track.items())
        },
        "property_class_status_counts": {
            key: dict(sorted(value.items()))
            for key, value in sorted(by_property_class.items())
        },
        "proof_family_counts": dict(sorted(proof_family_counts.items())),
        "readiness_counts": readiness_counts,
        "tasks": [item["task_ref"] for item in results],
        "missing_task_refs": missing_task_refs,
    }
    case_summary = {
        "benchmark": "verity-benchmark",
        "schema_version": 1,
        "unit": "case-secondary",
        "total_cases": len(case_rows),
        "status_counts": dict(sorted(Counter(item["status"] for item in case_rows).items())),
        "cases": case_rows,
    }
    return {"task_summary": task_summary, "case_summary": case_summary}


def main() -> int:
    parser = argparse.ArgumentParser(description="Task-oriented benchmark runner")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List task refs")
    list_parser.add_argument("--suite", choices=["active", "backlog", "all"], default="active")

    run_parser = subparsers.add_parser("run", help="Validate one hidden reference solution")
    run_parser.add_argument("task_ref")

    aggregate_parser = subparsers.add_parser("aggregate", help="Aggregate existing task results")
    aggregate_parser.add_argument("--suite", choices=["active", "backlog", "all"], default="active")
    aggregate_parser.add_argument("task_refs", nargs="*")

    args = parser.parse_args()

    if args.command == "list":
        for task_ref in discover_task_refs(args.suite):
            print(task_ref)
        return 0

    if args.command == "run":
        code, result_path = execute_reference_solution_task(args.task_ref)
        print(result_path.relative_to(ROOT))
        return code

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    aggregated = aggregate_results(args.task_refs, args.suite)
    (RESULTS_DIR / "summary.json").write_text(
        json.dumps(aggregated["task_summary"], indent=2) + "\n",
        encoding="utf-8",
    )
    (RESULTS_DIR / "case_summary.json").write_text(
        json.dumps(aggregated["case_summary"], indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
