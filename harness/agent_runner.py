#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from default_agent import (
    canonical_summary_path,
    config_label,
    execute_agent_task,
    resolve_config,
    resolve_config_path,
    scoped_summary_path,
    uses_legacy_aliases,
)
from task_runner import ROOT, discover_task_refs

RESULTS_DIR = ROOT / "results"
LEGACY_AGENT_SUMMARY_PATH = RESULTS_DIR / "agent_summary.json"


def resolve_case_task_refs(case_ref: str, suite: str) -> list[str]:
    parts = case_ref.split("/")
    if len(parts) != 2:
        raise SystemExit("usage: <project/case_id>")
    prefix = f"{case_ref}/"
    task_refs = [task_ref for task_ref in discover_task_refs(suite) if task_ref.startswith(prefix)]
    if not task_refs:
        raise SystemExit(f"no task manifests found for {case_ref} in suite {suite}")
    return task_refs


def run_many(task_refs: list[str], config_path: Path, dry_run: bool, *, profile: str | None, scope: str) -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    resolved_config = resolve_config(config_path, require_secrets=not dry_run, profile=profile)
    summary_path = scoped_summary_path(resolved_config, scope)
    entries: list[dict[str, object]] = []
    exit_code = 0

    for task_ref in task_refs:
        try:
            task_exit_code, result_path = execute_agent_task(
                config_path,
                task_ref,
                dry_run,
                profile=profile,
                resolved_config=resolved_config,
            )
            status = "dry_run" if dry_run else ("passed" if task_exit_code == 0 else "failed")
            if task_exit_code != 0:
                exit_code = 1
            entries.append(
                {
                    "task_ref": task_ref,
                    "status": status,
                    "artifact": str(result_path.relative_to(ROOT)),
                }
            )
            print(result_path.relative_to(ROOT))
        except SystemExit as exc:
            exit_code = 1
            entries.append(
                {
                    "task_ref": task_ref,
                    "status": "failed",
                    "error": str(exc),
                }
            )

    payload = {
        "schema_version": 1,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "scope": scope,
        "dry_run": dry_run,
        "profile": resolved_config.profile,
        "agent_id": resolved_config.agent_id,
        "track": resolved_config.track,
        "run_slug": resolved_config.run_slug,
        "config_path": config_label(config_path),
        "total_tasks": len(task_refs),
        "status_counts": dict(sorted(Counter(str(item["status"]) for item in entries).items())),
        "tasks": entries,
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if uses_legacy_aliases(resolved_config) and summary_path == canonical_summary_path(resolved_config):
        LEGACY_AGENT_SUMMARY_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return exit_code


def main() -> int:
    parser = argparse.ArgumentParser(description="Default benchmark agent runner")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List task refs for default-agent execution")
    list_parser.add_argument("--suite", choices=["active", "backlog", "all"], default="active")

    run_parser = subparsers.add_parser("run", help="Run the default agent for one task")
    run_parser.add_argument("task_ref")
    run_parser.add_argument("--config")
    run_parser.add_argument("--profile")
    run_parser.add_argument("--dry-run", action="store_true")

    case_parser = subparsers.add_parser("run-case", help="Run the default agent for every task in one case")
    case_parser.add_argument("case_ref")
    case_parser.add_argument("--suite", choices=["active", "backlog", "all"], default="active")
    case_parser.add_argument("--config")
    case_parser.add_argument("--profile")
    case_parser.add_argument("--dry-run", action="store_true")

    suite_parser = subparsers.add_parser("run-suite", help="Run the default agent for every task in a suite")
    suite_parser.add_argument("--suite", choices=["active", "backlog", "all"], default="active")
    suite_parser.add_argument("--config")
    suite_parser.add_argument("--profile")
    suite_parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    if args.command == "list":
        for task_ref in discover_task_refs(args.suite):
            print(task_ref)
        return 0

    config_path = resolve_config_path(getattr(args, "config", None), getattr(args, "profile", None))

    if args.command == "run":
        return run_many([args.task_ref], config_path, args.dry_run, profile=args.profile, scope="task")
    if args.command == "run-case":
        task_refs = resolve_case_task_refs(args.case_ref, args.suite)
        return run_many(task_refs, config_path, args.dry_run, profile=args.profile, scope=f"case:{args.case_ref}")

    task_refs = discover_task_refs(args.suite)
    return run_many(task_refs, config_path, args.dry_run, profile=args.profile, scope=f"suite:{args.suite}")


if __name__ == "__main__":
    raise SystemExit(main())
