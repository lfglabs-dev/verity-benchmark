#!/usr/bin/env python3
"""Run repeated benchmark comparisons between agent profiles.

Usage:
    python3 scripts/repeat_benchmark_compare.py run \
        --profiles openrouter-gemini-3.1-flash-lite-preview combined-lean-tools \
        --tasks ethereum/deposit_contract_minimal/deposit_count \
               kleros/sortition_trees/node_id_bijection \
        --repeats 3

    python3 scripts/repeat_benchmark_compare.py summary \
        --results-dir results/comparisons/latest
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run_single_task(
    profile: str,
    task_ref: str,
    *,
    repeat_index: int,
    results_dir: Path,
) -> dict:
    """Run a single task with a given profile and return the result summary."""
    start = time.perf_counter()
    cmd = [
        sys.executable,
        str(ROOT / "harness" / "agent_runner.py"),
        "run",
        task_ref,
        "--profile",
        profile,
    ]
    env = dict(os.environ)
    env["VERITY_REPEAT_INDEX"] = str(repeat_index)
    try:
        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=ROOT,
            env=env,
        )
    except subprocess.TimeoutExpired:
        return {
            "profile": profile,
            "task_ref": task_ref,
            "repeat": repeat_index,
            "status": "timeout",
            "elapsed_seconds": time.perf_counter() - start,
            "error": "timeout after 300s",
        }
    except Exception as exc:
        return {
            "profile": profile,
            "task_ref": task_ref,
            "repeat": repeat_index,
            "status": "error",
            "elapsed_seconds": time.perf_counter() - start,
            "error": str(exc),
        }

    elapsed = time.perf_counter() - start

    # Try to find and parse the result file
    result_path_line = completed.stdout.strip().splitlines()[-1] if completed.stdout.strip() else ""
    result_data = None
    if result_path_line:
        candidate = ROOT / result_path_line
        if candidate.is_file():
            try:
                result_data = json.loads(candidate.read_text(encoding="utf-8"))
            except Exception:
                pass

    status = "error"
    failure_mode = None
    eval_status = None
    if result_data:
        eval_status = result_data.get("evaluation", {}).get("status")
        failure_mode = result_data.get("evaluation", {}).get("failure_mode")
        status = eval_status or ("passed" if completed.returncode == 0 else "failed")

    summary = {
        "profile": profile,
        "task_ref": task_ref,
        "repeat": repeat_index,
        "status": status,
        "failure_mode": failure_mode,
        "elapsed_seconds": round(elapsed, 2),
        "exit_code": completed.returncode,
        "result_path": result_path_line or None,
    }

    if result_data:
        analysis = result_data.get("analysis", {})
        summary["attempt_count"] = analysis.get("attempt_count")
        summary["tool_calls_used"] = analysis.get("tool_calls_used", 0)

        # Token usage from last attempt or top-level
        usage = result_data.get("response", {}).get("usage", {})
        if not usage and result_data.get("attempts"):
            last_attempt = result_data["attempts"][-1]
            usage = last_attempt.get("response", {}).get("usage", {}) if isinstance(last_attempt.get("response"), dict) else {}
        summary["total_tokens"] = usage.get("total_tokens")
        summary["prompt_tokens"] = usage.get("prompt_tokens")
        summary["completion_tokens"] = usage.get("completion_tokens")

    return summary


def run_comparison(
    profiles: list[str],
    tasks: list[str],
    repeats: int,
    *,
    results_dir: Path,
    max_workers: int,
) -> dict:
    """Run a full comparison matrix."""
    results_dir.mkdir(parents=True, exist_ok=True)

    all_jobs: list[tuple[str, str, int]] = []
    for profile in profiles:
        for task_ref in tasks:
            for r in range(1, repeats + 1):
                all_jobs.append((profile, task_ref, r))

    results: list[dict] = []
    print(f"Running {len(all_jobs)} jobs ({len(profiles)} profiles x {len(tasks)} tasks x {repeats} repeats)")
    print(f"Max workers: {max_workers}")

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for profile, task_ref, r in all_jobs:
            future = executor.submit(
                run_single_task,
                profile,
                task_ref,
                repeat_index=r,
                results_dir=results_dir,
            )
            futures[future] = (profile, task_ref, r)

        for future in as_completed(futures):
            profile, task_ref, r = futures[future]
            try:
                result = future.result()
            except Exception as exc:
                result = {
                    "profile": profile,
                    "task_ref": task_ref,
                    "repeat": r,
                    "status": "error",
                    "error": str(exc),
                }
            results.append(result)
            status_icon = "+" if result["status"] == "passed" else "-"
            print(f"  [{status_icon}] {profile} / {task_ref} (r{r}): {result['status']} ({result.get('elapsed_seconds', '?')}s)")

    comparison = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "profiles": profiles,
        "tasks": tasks,
        "repeats": repeats,
        "results": results,
        "summary": build_summary(results, profiles, tasks),
    }

    output_path = results_dir / "comparison.json"
    output_path.write_text(json.dumps(comparison, indent=2) + "\n", encoding="utf-8")
    print(f"\nResults written to: {output_path}")
    return comparison


def build_summary(results: list[dict], profiles: list[str], tasks: list[str]) -> dict:
    """Build aggregate summary from comparison results."""
    summary: dict = {}
    for profile in profiles:
        profile_results = [r for r in results if r["profile"] == profile]
        passed = sum(1 for r in profile_results if r["status"] == "passed")
        total = len(profile_results)
        total_tokens = sum(r.get("total_tokens") or 0 for r in profile_results)
        total_elapsed = sum(r.get("elapsed_seconds") or 0 for r in profile_results)

        per_task: dict = {}
        for task_ref in tasks:
            task_results = [r for r in profile_results if r["task_ref"] == task_ref]
            task_passed = sum(1 for r in task_results if r["status"] == "passed")
            per_task[task_ref] = {
                "passed": task_passed,
                "total": len(task_results),
                "pass_rate": round(task_passed / max(len(task_results), 1), 3),
            }

        summary[profile] = {
            "passed": passed,
            "total": total,
            "pass_rate": round(passed / max(total, 1), 3),
            "total_tokens": total_tokens,
            "total_elapsed_seconds": round(total_elapsed, 2),
            "per_task": per_task,
        }
    return summary


def print_summary(comparison: dict) -> None:
    """Print a readable summary table."""
    summary = comparison.get("summary", {})
    profiles = comparison.get("profiles", [])
    tasks = comparison.get("tasks", [])

    print("\n=== Comparison Summary ===\n")
    header = f"{'Profile':<45} {'Pass':>5} {'Total':>5} {'Rate':>6} {'Tokens':>8} {'Time':>7}"
    print(header)
    print("-" * len(header))
    for profile in profiles:
        s = summary.get(profile, {})
        print(
            f"{profile:<45} {s.get('passed', 0):>5} {s.get('total', 0):>5} "
            f"{s.get('pass_rate', 0):>6.1%} {s.get('total_tokens', 0):>8} "
            f"{s.get('total_elapsed_seconds', 0):>6.1f}s"
        )

    print(f"\n{'Per-task breakdown:'}")
    for task_ref in tasks:
        print(f"\n  {task_ref}:")
        for profile in profiles:
            pt = summary.get(profile, {}).get("per_task", {}).get(task_ref, {})
            print(f"    {profile:<40} {pt.get('passed', 0)}/{pt.get('total', 0)} ({pt.get('pass_rate', 0):.0%})")


DEFAULT_SUBSET_TASKS = [
    "ethereum/deposit_contract_minimal/deposit_count",
    "kleros/sortition_trees/node_id_bijection",
    "paladin_votes/stream_recovery_claim_usdc/claim_marks_user",
]

CONFIRMATION_TASKS = [
    "ethereum/deposit_contract_minimal/deposit_count",
    "ethereum/deposit_contract_minimal/chain_start_threshold",
    "kleros/sortition_trees/node_id_bijection",
    "nexus_mutual/ramm_price_band/sync_sets_book_value",
    "paladin_votes/stream_recovery_claim_usdc/claim_marks_user",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark comparison runner")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run benchmark comparison")
    run_parser.add_argument("--profiles", nargs="+", required=True)
    run_parser.add_argument("--tasks", nargs="+", default=None,
                           help="Task refs to benchmark (default: 3-task subset)")
    run_parser.add_argument("--repeats", type=int, default=1)
    run_parser.add_argument("--results-dir", type=str, default=None)
    run_parser.add_argument("--max-workers", type=int, default=3)
    run_parser.add_argument("--confirmation", action="store_true",
                           help="Use the 5-task confirmation slice")

    summary_parser = subparsers.add_parser("summary", help="Print summary from results")
    summary_parser.add_argument("--results-dir", type=str, required=True)

    args = parser.parse_args()

    if args.command == "run":
        tasks = args.tasks
        if tasks is None:
            tasks = CONFIRMATION_TASKS if args.confirmation else DEFAULT_SUBSET_TASKS
        results_dir = Path(args.results_dir) if args.results_dir else (
            ROOT / "results" / "comparisons" / datetime.now().strftime("%Y%m%d-%H%M%S")
        )
        comparison = run_comparison(
            args.profiles,
            tasks,
            args.repeats,
            results_dir=results_dir,
            max_workers=args.max_workers,
        )
        print_summary(comparison)
        return 0

    if args.command == "summary":
        results_dir = Path(args.results_dir)
        comparison_path = results_dir / "comparison.json"
        if not comparison_path.is_file():
            print(f"No comparison.json found in {results_dir}", file=sys.stderr)
            return 1
        comparison = json.loads(comparison_path.read_text(encoding="utf-8"))
        print_summary(comparison)
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
