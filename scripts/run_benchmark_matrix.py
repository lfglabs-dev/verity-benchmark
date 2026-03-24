#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
HARNESS_DIR = ROOT / "harness"
if str(HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(HARNESS_DIR))

from default_agent import load_config  # type: ignore
from task_runner import discover_task_refs  # type: ignore

README_PATH = ROOT / "README.md"
MATRIX_RESULTS_DIR = ROOT / "results" / "matrix"
MATRIX_RUNS_DIR = MATRIX_RESULTS_DIR / "runs"
MATRIX_README_START = "<!-- BENCHMARK_MATRIX:START -->"
MATRIX_README_END = "<!-- BENCHMARK_MATRIX:END -->"


@dataclass(frozen=True)
class BenchmarkTarget:
    key: str
    config_path: Path
    repeats: int


TARGET_CONFIGS: dict[str, Path] = {
    "builtin-fast": ROOT / "harness/agents/default.json",
    "builtin-smart": ROOT / "harness/agents/builtin-smart.json",
    "openrouter-gemini-3.1-flash-lite-preview": ROOT / "harness/agents/openrouter-gemini-3.1-flash-lite-preview.json",
    "leanstral": ROOT / "harness/agents/leanstral.json",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def slugify(text: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in text).strip("-").lower()


def task_to_module(task_ref: str) -> str:
    parts = task_ref.split("/")
    if len(parts) < 2:
        raise ValueError(f"invalid task ref {task_ref!r}")
    return f"{parts[0]}/{parts[1]}"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    tmp_path.replace(path)


def format_average(value: float) -> str:
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{value:.1f}"


def format_seconds(seconds: float) -> str:
    return f"{seconds:.1f}s"


def format_tokens(tokens: float) -> str:
    if abs(tokens - round(tokens)) < 1e-9:
        return f"{int(round(tokens)):,}"
    return f"{tokens:,.1f}"


def extract_tokens(task_payload: dict[str, Any]) -> int:
    response = task_payload.get("response")
    if not isinstance(response, dict):
        return 0
    usage = response.get("usage")
    if not isinstance(usage, dict):
        return 0
    total_tokens = usage.get("total_tokens")
    if isinstance(total_tokens, int):
        return total_tokens
    return 0


def build_temp_config(base_config_path: Path, run_slug: str, state_dir: Path) -> Path:
    config = load_config(base_config_path)
    config["run_slug"] = run_slug
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".json",
        prefix=f"{slugify(run_slug)}-",
        delete=False,
        dir=str(state_dir / "tmp"),
        encoding="utf-8",
    )
    with handle:
        json.dump(config, handle, indent=2)
        handle.write("\n")
    return Path(handle.name)


def run_suite(config_path: Path, *, log_handle: Any) -> Path:
    config = load_config(config_path)
    summary_path = ROOT / "results" / "agent_summaries" / str(config["track"]) / f"{config['run_slug']}.json"
    command = [
        str(ROOT / "scripts" / "exec_with_dotenvx.sh"),
        "python3",
        "harness/agent_runner.py",
        "run-suite",
        "--suite",
        "all",
        "--config",
        relative(config_path),
    ]
    return_code = subprocess.call(command, cwd=ROOT, stdout=log_handle, stderr=subprocess.STDOUT)
    if return_code != 0 and not summary_path.is_file():
        raise SystemExit(f"run-suite failed with exit code {return_code}")
    return summary_path


def benchmark_target(key: str, repeats: int) -> BenchmarkTarget:
    config_path = TARGET_CONFIGS.get(key)
    if config_path is None:
        raise SystemExit(f"unknown target key {key!r}")
    return BenchmarkTarget(key=key, config_path=config_path, repeats=repeats)


def target_specs(args: argparse.Namespace) -> list[BenchmarkTarget]:
    requested_keys = list(args.target_key) if getattr(args, "target_key", None) else list(TARGET_CONFIGS)
    repeat_map = {
        "builtin-fast": args.fast_repeats,
        "builtin-smart": args.smart_repeats,
        "openrouter-gemini-3.1-flash-lite-preview": args.openrouter_repeats,
        "leanstral": args.leanstral_repeats,
    }
    return [benchmark_target(key, repeat_map[key]) for key in requested_keys]


def resolve_state_dir(run_id: str | None) -> Path:
    if run_id:
        state_dir = MATRIX_RUNS_DIR / run_id
        if not state_dir.is_dir():
            raise SystemExit(f"matrix run not found: {relative(state_dir)}")
        return state_dir
    latest_path = MATRIX_RESULTS_DIR / "latest-run.txt"
    if not latest_path.is_file():
        raise SystemExit("no matrix run found; start one first")
    latest_run_id = latest_path.read_text(encoding="utf-8").strip()
    if not latest_run_id:
        raise SystemExit("latest matrix run marker is empty")
    state_dir = MATRIX_RUNS_DIR / latest_run_id
    if not state_dir.is_dir():
        raise SystemExit(f"latest matrix run directory missing: {relative(state_dir)}")
    return state_dir


def write_latest_run(run_id: str) -> None:
    MATRIX_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (MATRIX_RESULTS_DIR / "latest-run.txt").write_text(run_id + "\n", encoding="utf-8")


def spawn_worker(state_dir: Path, run_id: str, target_key: str, log_path: Path) -> int:
    script_path = ROOT / "scripts" / "run_benchmark_matrix.py"
    env = os.environ.copy()
    worker_command = [
        "python3",
        str(script_path),
        "worker",
        "--run-id",
        run_id,
        "--target-key",
        target_key,
    ]
    with log_path.open("a", encoding="utf-8") as log_handle:
        process = subprocess.Popen(
            worker_command,
            cwd=ROOT,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            env=env,
        )
    return process.pid


def pid_is_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def process_state(pid: int) -> str:
    status_path = Path("/proc") / str(pid) / "status"
    if not status_path.is_file():
        return "exited"
    for line in status_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("State:"):
            parts = line.split()
            if len(parts) >= 2 and parts[1] == "T":
                return "paused"
            if len(parts) >= 2 and parts[1] == "Z":
                return "exited"
            return "running"
    return "running"


def normalize_worker_status(worker: dict[str, Any]) -> str:
    status = str(worker.get("status", "unknown"))
    pid = int(worker.get("pid", 0))
    if status != "running":
        return status
    if pid <= 0:
        return "failed"
    runtime_state = process_state(pid)
    if runtime_state == "exited":
        return "failed"
    if runtime_state == "paused":
        return "paused"
    return "running"


def discover_modules() -> list[str]:
    return sorted({task_to_module(task_ref) for task_ref in discover_task_refs("all")})


def load_summary(summary_path: Path) -> dict[str, Any]:
    if not summary_path.is_file():
        raise SystemExit(f"missing summary file: {relative(summary_path)}")
    return load_json(summary_path)


def collect_run_metrics(summary: dict[str, Any], modules: list[str]) -> tuple[dict[str, dict[str, int]], float, int]:
    module_counts: dict[str, dict[str, int]] = {module: {"passed": 0, "failed": 0} for module in modules}
    total_elapsed_seconds = 0.0
    total_tokens = 0

    for task_entry in summary.get("tasks", []):
        if not isinstance(task_entry, dict):
            continue
        task_ref = str(task_entry.get("task_ref"))
        module = task_to_module(task_ref)
        summary_status = str(task_entry.get("status"))
        artifact = task_entry.get("artifact")
        if not isinstance(artifact, str):
            if summary_status == "passed":
                module_counts[module]["passed"] += 1
            else:
                module_counts[module]["failed"] += 1
            continue
        task_result = load_json(ROOT / artifact)
        status = str(task_result.get("status"))
        if status == "passed":
            module_counts[module]["passed"] += 1
        else:
            module_counts[module]["failed"] += 1
        elapsed = task_result.get("elapsed_seconds")
        if isinstance(elapsed, (int, float)):
            total_elapsed_seconds += float(elapsed)
        total_tokens += extract_tokens(task_result)

    return module_counts, round(total_elapsed_seconds, 3), total_tokens


def worker_state_path(state_dir: Path, target_key: str) -> Path:
    return state_dir / "workers" / f"{target_key}.json"


def load_worker_state(state_dir: Path, target_key: str) -> dict[str, Any]:
    path = worker_state_path(state_dir, target_key)
    if not path.is_file():
        raise SystemExit(f"worker state not found: {relative(path)}")
    return load_json(path)


def write_worker_state(state_dir: Path, target_key: str, payload: dict[str, Any]) -> None:
    write_json(worker_state_path(state_dir, target_key), payload)


def default_report_path(state_dir: Path) -> Path:
    return state_dir / "benchmark-matrix.json"


def aggregate_state(state_dir: Path) -> dict[str, Any]:
    state = load_json(state_dir / "state.json")
    modules = discover_modules()
    targets: list[dict[str, Any]] = []

    for target in state["targets"]:
        worker = load_worker_state(state_dir, target["key"])
        completed_runs = [run for run in worker.get("runs", []) if run.get("status") == "completed"]
        module_averages = {module: {"passed": 0.0, "failed": 0.0} for module in modules}
        average_elapsed_seconds = 0.0
        average_tokens = 0.0

        if completed_runs:
            for run in completed_runs:
                summary = load_summary(ROOT / str(run["summary_path"]))
                module_counts, elapsed_seconds, total_tokens = collect_run_metrics(summary, modules)
                for module in modules:
                    module_averages[module]["passed"] += module_counts[module]["passed"]
                    module_averages[module]["failed"] += module_counts[module]["failed"]
                average_elapsed_seconds += elapsed_seconds
                average_tokens += total_tokens

            run_count = len(completed_runs)
            for module in modules:
                module_averages[module]["passed"] /= run_count
                module_averages[module]["failed"] /= run_count
            average_elapsed_seconds /= run_count
            average_tokens /= run_count

        targets.append(
            {
                "key": target["key"],
                "model": target["model"],
                "repeats": target["repeats"],
                "completed_runs": len(completed_runs),
                "status": normalize_worker_status(worker),
                "modules": module_averages,
                "average_total_elapsed_seconds": average_elapsed_seconds,
                "average_total_tokens": average_tokens,
                "log_path": worker.get("log_path"),
                "runs": worker.get("runs", []),
            }
        )

    return {
        "schema_version": 2,
        "run_id": state["run_id"],
        "created_at": state["created_at"],
        "updated_at": utc_now(),
        "modules": modules,
        "targets": targets,
    }


def build_markdown(report: dict[str, Any]) -> str:
    targets = report["targets"]
    modules = report["modules"]
    headers = ["Module"] + [target["model"] for target in targets]
    lines = [
        "## Benchmark Results",
        "",
        "Generated by `python3 scripts/run_benchmark_matrix.py render`.",
        "",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]

    for module in modules:
        row = [module]
        for target in targets:
            if target["status"] == "failed":
                row.append("failed")
                continue
            if target["completed_runs"] == 0:
                row.append("pending")
                continue
            counts = target["modules"][module]
            row.append(f"{format_average(counts['passed'])}/{format_average(counts['failed'])}")
        lines.append("| " + " | ".join(row) + " |")

    total_row = ["Total time / tokens"]
    for target in targets:
        if target["status"] == "failed":
            total_row.append("failed")
            continue
        if target["completed_runs"] == 0:
            total_row.append("pending")
            continue
        total_row.append(
            f"{format_seconds(target['average_total_elapsed_seconds'])} / "
            f"{format_tokens(target['average_total_tokens'])}"
        )
    lines.append("| " + " | ".join(total_row) + " |")
    return "\n".join(lines) + "\n"


def update_readme(markdown: str) -> None:
    content = README_PATH.read_text(encoding="utf-8")
    start = content.find(MATRIX_README_START)
    end = content.find(MATRIX_README_END)
    if start == -1 or end == -1 or end < start:
        raise SystemExit("README benchmark matrix markers not found")
    replacement = f"{MATRIX_README_START}\n{markdown}{MATRIX_README_END}"
    updated = content[:start] + replacement + content[end + len(MATRIX_README_END):]
    README_PATH.write_text(updated, encoding="utf-8")


def command_start(args: argparse.Namespace) -> int:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    state_dir = MATRIX_RUNS_DIR / run_id
    if state_dir.exists():
        raise SystemExit(f"matrix run already exists: {relative(state_dir)}")

    targets = target_specs(args)
    state_dir.mkdir(parents=True, exist_ok=False)
    (state_dir / "logs").mkdir(parents=True, exist_ok=True)
    (state_dir / "workers").mkdir(parents=True, exist_ok=True)
    (state_dir / "tmp").mkdir(parents=True, exist_ok=True)

    state_payload = {
        "schema_version": 2,
        "run_id": run_id,
        "created_at": utc_now(),
        "targets": [],
    }

    for target in targets:
        config = load_config(target.config_path)
        log_path = state_dir / "logs" / f"{target.key}.log"
        worker_payload = {
            "schema_version": 2,
            "target_key": target.key,
            "status": "starting",
            "pid": 0,
            "model": str(config["model"]),
            "repeats": target.repeats,
            "completed_runs": 0,
            "current_run_index": 1 if target.repeats > 0 else 0,
            "log_path": relative(log_path),
            "started_at": utc_now(),
            "runs": [],
        }
        write_worker_state(state_dir, target.key, worker_payload)
        state_payload["targets"].append(
            {
                "key": target.key,
                "model": str(config["model"]),
                "config_path": relative(target.config_path),
                "repeats": target.repeats,
                "log_path": relative(log_path),
                "worker_state_path": relative(worker_state_path(state_dir, target.key)),
            }
        )

    write_json(state_dir / "state.json", state_payload)
    write_latest_run(run_id)

    for target in targets:
        log_path = state_dir / "logs" / f"{target.key}.log"
        pid = spawn_worker(state_dir, run_id, target.key, log_path)
        worker = load_worker_state(state_dir, target.key)
        worker.update({"status": "running", "pid": pid})
        write_worker_state(state_dir, target.key, worker)
    print(f"started matrix run {run_id}")
    print(relative(state_dir))
    return 0


def command_add_target(args: argparse.Namespace) -> int:
    state_dir = resolve_state_dir(args.run_id)
    state = load_json(state_dir / "state.json")
    existing_keys = {str(item["key"]) for item in state["targets"]}
    if args.target_key in existing_keys:
        raise SystemExit(f"target {args.target_key!r} already exists in run {state['run_id']}")

    target = benchmark_target(args.target_key, args.repeats)
    config = load_config(target.config_path)
    log_path = state_dir / "logs" / f"{target.key}.log"
    worker_payload = {
        "schema_version": 2,
        "target_key": target.key,
        "status": "starting",
        "pid": 0,
        "model": str(config["model"]),
        "repeats": target.repeats,
        "completed_runs": 0,
        "current_run_index": 1 if target.repeats > 0 else 0,
        "log_path": relative(log_path),
        "started_at": utc_now(),
        "runs": [],
    }
    write_worker_state(state_dir, target.key, worker_payload)
    state["targets"].append(
        {
            "key": target.key,
            "model": str(config["model"]),
            "config_path": relative(target.config_path),
            "repeats": target.repeats,
            "log_path": relative(log_path),
            "worker_state_path": relative(worker_state_path(state_dir, target.key)),
        }
    )
    write_json(state_dir / "state.json", state)

    pid = spawn_worker(state_dir, state["run_id"], target.key, log_path)
    worker_payload.update({"status": "running", "pid": pid})
    write_worker_state(state_dir, target.key, worker_payload)
    print(f"{target.key}: started pid={pid}")
    return 0


def command_retry_target(args: argparse.Namespace) -> int:
    state_dir = resolve_state_dir(args.run_id)
    state = load_json(state_dir / "state.json")
    target_info = next((item for item in state["targets"] if item["key"] == args.target_key), None)
    if target_info is None:
        raise SystemExit(f"unknown target key {args.target_key!r}")

    worker = load_worker_state(state_dir, args.target_key)
    pid = int(worker.get("pid", 0))
    if worker.get("status") == "running" and pid > 0 and pid_is_alive(pid):
        raise SystemExit(f"target {args.target_key!r} is still running")

    log_path = ROOT / str(worker["log_path"])
    if args.clear_log:
        log_path.write_text("", encoding="utf-8")

    worker.pop("error", None)
    worker.pop("failed_at", None)
    worker.pop("finished_at", None)
    worker.update(
        {
            "status": "running",
            "pid": 0,
            "completed_runs": 0,
            "current_run_index": 1 if int(worker.get("repeats", 0)) > 0 else 0,
            "started_at": utc_now(),
            "runs": [],
        }
    )
    write_worker_state(state_dir, args.target_key, worker)

    pid = spawn_worker(state_dir, state["run_id"], args.target_key, log_path)
    worker["pid"] = pid
    write_worker_state(state_dir, args.target_key, worker)
    print(f"{args.target_key}: restarted pid={pid}")
    return 0


def command_worker(args: argparse.Namespace) -> int:
    state_dir = resolve_state_dir(args.run_id)
    state = load_json(state_dir / "state.json")
    target_info = next((item for item in state["targets"] if item["key"] == args.target_key), None)
    if target_info is None:
        raise SystemExit(f"unknown target key {args.target_key!r}")

    target = BenchmarkTarget(
        key=str(target_info["key"]),
        config_path=ROOT / str(target_info["config_path"]),
        repeats=int(target_info["repeats"]),
    )
    base_config = load_config(target.config_path)
    worker = load_worker_state(state_dir, target.key)
    log_path = ROOT / str(worker["log_path"])
    with log_path.open("a", encoding="utf-8") as log_handle:
        log_handle.write(f"[{utc_now()}] worker started for {target.key}\n")
        log_handle.flush()
        runs = list(worker.get("runs", []))
        start_index = len(runs) + 1

        for index in range(start_index, target.repeats + 1):
            run_slug = f"{base_config['run_slug']}-run-{index}"
            temp_config = build_temp_config(target.config_path, run_slug, state_dir)
            run_record = {
                "run_index": index,
                "run_slug": run_slug,
                "status": "running",
                "config_path": relative(temp_config),
                "started_at": utc_now(),
            }
            runs.append(run_record)
            worker.update(
                {
                    "status": "running",
                    "pid": os.getpid(),
                    "current_run_index": index,
                    "runs": runs,
                }
            )
            write_worker_state(state_dir, target.key, worker)
            log_handle.write(f"[{utc_now()}] starting run {index}/{target.repeats}: {run_slug}\n")
            log_handle.flush()

            try:
                summary_path = run_suite(temp_config, log_handle=log_handle)
                run_record.update(
                    {
                        "status": "completed",
                        "summary_path": relative(summary_path),
                        "finished_at": utc_now(),
                    }
                )
                worker["completed_runs"] = int(worker.get("completed_runs", 0)) + 1
                write_worker_state(state_dir, target.key, worker)
                log_handle.write(f"[{utc_now()}] completed run {index}/{target.repeats}: {relative(summary_path)}\n")
                log_handle.flush()
            except BaseException as exc:
                run_record.update(
                    {
                        "status": "failed",
                        "error": str(exc),
                        "finished_at": utc_now(),
                    }
                )
                worker.update({"status": "failed", "runs": runs, "failed_at": utc_now(), "error": str(exc)})
                worker["pid"] = 0
                write_worker_state(state_dir, target.key, worker)
                log_handle.write(f"[{utc_now()}] worker failed: {exc}\n")
                log_handle.flush()
                return 1
            finally:
                temp_config.unlink(missing_ok=True)

        worker.update(
            {
                "status": "completed",
                "pid": 0,
                "current_run_index": 0,
                "finished_at": utc_now(),
                "runs": runs,
            }
        )
        write_worker_state(state_dir, target.key, worker)
        log_handle.write(f"[{utc_now()}] worker completed for {target.key}\n")
        log_handle.flush()
    return 0


def command_status(args: argparse.Namespace) -> int:
    state_dir = resolve_state_dir(args.run_id)
    state = load_json(state_dir / "state.json")
    print(f"run_id: {state['run_id']}")
    print(f"state_dir: {relative(state_dir)}")

    for target in state["targets"]:
        worker = load_worker_state(state_dir, target["key"])
        pid = int(worker.get("pid", 0))
        derived_status = normalize_worker_status(worker)
        completed_runs = int(worker.get("completed_runs", 0))
        repeats = int(worker.get("repeats", 0))
        print(
            f"{target['key']}: {derived_status} "
            f"runs={completed_runs}/{repeats} pid={pid or '-'} log={worker.get('log_path')}"
        )
        runs = worker.get("runs", [])
        if runs:
            latest = runs[-1]
            latest_status = latest.get("status", "unknown")
            latest_slug = latest.get("run_slug", "-")
            print(f"  latest_run={latest_slug} status={latest_status}")
        if args.verbose and worker.get("error"):
            print(f"  error={worker['error']}")
    return 0


def control_workers(run_id: str | None, target_key: str | None, signal_name: int, verb: str) -> int:
    state_dir = resolve_state_dir(run_id)
    state = load_json(state_dir / "state.json")
    selected = [item for item in state["targets"] if target_key in {None, item["key"]}]
    if not selected:
        raise SystemExit(f"no targets matched {target_key!r}")

    for target in selected:
        worker = load_worker_state(state_dir, target["key"])
        pid = int(worker.get("pid", 0))
        if pid <= 0 or not pid_is_alive(pid):
            print(f"{target['key']}: not running")
            continue
        try:
            os.killpg(os.getpgid(pid), signal_name)
        except ProcessLookupError:
            print(f"{target['key']}: not running")
            continue
        print(f"{target['key']}: {verb}")
    return 0


def command_pause(args: argparse.Namespace) -> int:
    return control_workers(args.run_id, args.target_key, signal.SIGSTOP, "paused")


def command_resume(args: argparse.Namespace) -> int:
    return control_workers(args.run_id, args.target_key, signal.SIGCONT, "resumed")


def command_stop(args: argparse.Namespace) -> int:
    return control_workers(args.run_id, args.target_key, signal.SIGTERM, "stopped")


def command_logs(args: argparse.Namespace) -> int:
    state_dir = resolve_state_dir(args.run_id)
    state = load_json(state_dir / "state.json")
    targets = [item for item in state["targets"] if args.target_key in {None, item["key"]}]
    if not targets:
        raise SystemExit(f"no targets matched {args.target_key!r}")

    for target in targets:
        worker = load_worker_state(state_dir, target["key"])
        log_path = ROOT / str(worker["log_path"])
        print(f"== {target['key']} ({relative(log_path)}) ==")
        if not log_path.is_file():
            print("<missing log>")
            continue
        lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
        for line in lines[-args.lines :]:
            print(line)
    return 0


def command_render(args: argparse.Namespace) -> int:
    state_dir = resolve_state_dir(args.run_id)
    report = aggregate_state(state_dir)
    report_path = default_report_path(state_dir)
    write_json(report_path, report)

    MATRIX_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    write_json(MATRIX_RESULTS_DIR / "latest.json", report)
    shutil.copyfile(report_path, MATRIX_RESULTS_DIR / "benchmark-matrix.json")

    markdown = build_markdown(report)
    (state_dir / "README-benchmark-results.md").write_text(markdown, encoding="utf-8")
    (MATRIX_RESULTS_DIR / "README-benchmark-results.md").write_text(markdown, encoding="utf-8")
    update_readme(markdown)
    print(relative(report_path))
    return 0


def command_wait(args: argparse.Namespace) -> int:
    state_dir = resolve_state_dir(args.run_id)
    timeout_at = time.time() + args.timeout_seconds if args.timeout_seconds > 0 else None

    while True:
        state = load_json(state_dir / "state.json")
        workers = [load_worker_state(state_dir, target["key"]) for target in state["targets"]]
        statuses: list[str] = []
        for worker in workers:
            derived_status = normalize_worker_status(worker)
            if str(worker.get("status")) == "running" and derived_status == "failed":
                worker["status"] = "failed"
                worker["pid"] = 0
                worker["failed_at"] = utc_now()
                worker.setdefault("error", "worker exited unexpectedly before writing final state")
                write_worker_state(state_dir, str(worker["target_key"]), worker)
            statuses.append(derived_status)
        if all(status in {"completed", "failed"} for status in statuses):
            break
        if timeout_at is not None and time.time() >= timeout_at:
            raise SystemExit("timed out waiting for matrix run to finish")
        time.sleep(args.poll_seconds)

    render_result = command_render(argparse.Namespace(run_id=state_dir.name))
    failed_targets = [worker["target_key"] for worker in workers if str(worker.get("status")) == "failed"]
    if failed_targets:
        print("matrix targets failed: " + ", ".join(failed_targets), file=sys.stderr)
        return 1
    return render_result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run repeated benchmark suites in parallel and refresh the README matrix.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    start_parser = subparsers.add_parser("start", help="Start a new matrix run in the background")
    start_parser.add_argument("--fast-repeats", type=int, default=3)
    start_parser.add_argument("--smart-repeats", type=int, default=3)
    start_parser.add_argument("--openrouter-repeats", type=int, default=1)
    start_parser.add_argument("--leanstral-repeats", type=int, default=1)
    start_parser.add_argument(
        "--target-key",
        action="append",
        choices=sorted(TARGET_CONFIGS),
        help="Restrict the started run to one or more named targets",
    )

    worker_parser = subparsers.add_parser("worker", help=argparse.SUPPRESS)
    worker_parser.add_argument("--run-id", required=True)
    worker_parser.add_argument("--target-key", required=True)

    status_parser = subparsers.add_parser("status", help="Show matrix worker status")
    status_parser.add_argument("--run-id")
    status_parser.add_argument("--verbose", action="store_true")

    pause_parser = subparsers.add_parser("pause", help="Pause one or all running matrix workers")
    pause_parser.add_argument("--run-id")
    pause_parser.add_argument("--target-key")

    resume_parser = subparsers.add_parser("resume", help="Resume one or all paused matrix workers")
    resume_parser.add_argument("--run-id")
    resume_parser.add_argument("--target-key")

    stop_parser = subparsers.add_parser("stop", help="Stop one or all matrix workers")
    stop_parser.add_argument("--run-id")
    stop_parser.add_argument("--target-key")

    logs_parser = subparsers.add_parser("logs", help="Show recent matrix worker logs")
    logs_parser.add_argument("--run-id")
    logs_parser.add_argument("--target-key")
    logs_parser.add_argument("-n", "--lines", type=int, default=40)

    render_parser = subparsers.add_parser("render", help="Aggregate completed runs and refresh the README table")
    render_parser.add_argument("--run-id")

    wait_parser = subparsers.add_parser("wait", help="Wait for the latest run to finish, then render the README table")
    wait_parser.add_argument("--run-id")
    wait_parser.add_argument("--poll-seconds", type=int, default=30)
    wait_parser.add_argument("--timeout-seconds", type=int, default=0)

    retry_parser = subparsers.add_parser("retry-target", help="Restart one failed or stopped matrix worker")
    retry_parser.add_argument("--run-id")
    retry_parser.add_argument("--target-key", required=True)
    retry_parser.add_argument("--clear-log", action="store_true")

    add_target_parser = subparsers.add_parser("add-target", help="Add and start a new target in an existing matrix run")
    add_target_parser.add_argument("--run-id")
    add_target_parser.add_argument("--target-key", required=True, choices=sorted(TARGET_CONFIGS))
    add_target_parser.add_argument("--repeats", type=int, default=1)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "start":
        return command_start(args)
    if args.command == "worker":
        return command_worker(args)
    if args.command == "status":
        return command_status(args)
    if args.command == "pause":
        return command_pause(args)
    if args.command == "resume":
        return command_resume(args)
    if args.command == "stop":
        return command_stop(args)
    if args.command == "logs":
        return command_logs(args)
    if args.command == "render":
        return command_render(args)
    if args.command == "wait":
        return command_wait(args)
    if args.command == "retry-target":
        return command_retry_target(args)
    if args.command == "add-target":
        return command_add_target(args)
    raise SystemExit(f"unsupported command {args.command!r}")


if __name__ == "__main__":
    raise SystemExit(main())
