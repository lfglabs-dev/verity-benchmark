#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, OrderedDict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent

FAILURE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("theorem_statement_mismatch", re.compile(r"changed the editable theorem statement|theorem statement mismatch", re.I)),
    ("empty_response", re.compile(r"empty response", re.I)),
    ("placeholder", re.compile(r"\bsorry\b|placeholder", re.I)),
    ("hidden_case_import_detected", re.compile(r"hidden_case_import_detected|hidden import", re.I)),
    ("lean_check_failed", re.compile(r"CandidateCheck\.lean:|unsolved goals|type mismatch|simp made no progress|error:", re.I)),
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def classify_failure(payload: dict[str, Any]) -> str:
    evaluation = payload.get("evaluation")
    details = ""
    if isinstance(evaluation, dict):
        failure_mode = evaluation.get("failure_mode")
        if isinstance(failure_mode, str) and failure_mode:
            return failure_mode
        maybe_details = evaluation.get("details")
        if isinstance(maybe_details, str):
            details = maybe_details
    response_text = payload.get("response_text")
    if isinstance(response_text, str):
        details += "\n" + response_text
    for label, pattern in FAILURE_PATTERNS:
        if pattern.search(details):
            return label
    return "other"


def artifact_path(task_entry: dict[str, Any]) -> Path:
    return ROOT / task_entry["artifact"]


def attempt_has_candidate_state(attempt: dict[str, Any]) -> bool:
    candidate_text = attempt.get("candidate_file_contents")
    if isinstance(candidate_text, str) and candidate_text.strip():
        return True
    evaluation = attempt.get("evaluation")
    if not isinstance(evaluation, dict):
        return False
    status = evaluation.get("status")
    failure_mode = evaluation.get("failure_mode")
    return bool((isinstance(status, str) and status) or (isinstance(failure_mode, str) and failure_mode))


def summarize_summary_file(summary_path: Path) -> None:
    data = load_json(summary_path)
    by_module: OrderedDict[str, dict[str, int]] = OrderedDict()
    failure_modes: Counter[str] = Counter()
    retry_histogram: Counter[int] = Counter()
    models: Counter[str] = Counter()
    reasoning_attempts = 0
    candidate_changes = 0
    failure_mode_changes = 0
    solved_after_retry = 0

    for task in data["tasks"]:
        task_ref = task["task_ref"]
        module = "/".join(task_ref.split("/")[:2])
        bucket = by_module.setdefault(module, {"passed": 0, "failed": 0})
        bucket[task["status"]] += 1

        payload = load_json(artifact_path(task))
        response = payload.get("response")
        if isinstance(response, dict):
            model = response.get("model")
            if isinstance(model, str) and model:
                models[model] += 1

        attempts = payload.get("attempts")
        if isinstance(attempts, list):
            proof_attempts = [attempt for attempt in attempts if isinstance(attempt, dict) and attempt_has_candidate_state(attempt)]
            retry_histogram[len(attempts)] += 1
            if task["status"] == "passed" and len(proof_attempts) > 1:
                solved_after_retry += 1
            for attempt in attempts:
                trace = attempt.get("trace")
                if not isinstance(trace, dict):
                    continue
                if int(trace.get("provider_reasoning_chars") or 0) > 0:
                    reasoning_attempts += 1
                if trace.get("candidate_changed_from_previous") is True:
                    candidate_changes += 1
                if trace.get("failure_mode_changed_from_previous") is True:
                    failure_mode_changes += 1

        if task["status"] == "failed":
            failure_modes[classify_failure(payload)] += 1

    print(f"summary: {summary_path}")
    print(f"run_slug: {data['run_slug']}")
    print(f"total: {data['total_tasks']} passed={data['status_counts'].get('passed', 0)} failed={data['status_counts'].get('failed', 0)}")
    print("by_module:")
    for module, counts in by_module.items():
        print(f"  {module}: {counts['passed']} passed / {counts['failed']} failed")
    if failure_modes:
        print("failure_modes:")
        for label, count in failure_modes.most_common():
            print(f"  {label}: {count}")
    if retry_histogram:
        print("attempt_histogram:")
        for attempt_count, count in sorted(retry_histogram.items()):
            print(f"  {attempt_count} attempts: {count} tasks")
        print("retry_productivity:")
        print(f"  solved_after_retry: {solved_after_retry}")
        print(f"  candidate_changes: {candidate_changes}")
        print(f"  failure_mode_changes: {failure_mode_changes}")
        print(f"  attempts_with_provider_reasoning: {reasoning_attempts}")
    if models:
        print("response_models:")
        for model, count in models.most_common():
            print(f"  {model}: {count}")


def summarize_artifact_dir(artifact_dir: Path) -> None:
    if not artifact_dir.is_dir():
        raise SystemExit(f"artifact directory not found: {artifact_dir}")

    by_module: OrderedDict[str, dict[str, int]] = OrderedDict()
    failure_modes: Counter[str] = Counter()
    retry_histogram: Counter[int] = Counter()
    models: Counter[str] = Counter()
    reasoning_attempts = 0
    candidate_changes = 0
    failure_mode_changes = 0
    solved_after_retry = 0

    files = sorted(artifact_dir.glob("*.json"))
    for path in files:
        payload = load_json(path)
        stem_parts = path.stem.split("__")
        module = "/".join(stem_parts[:2])
        evaluation = payload.get("evaluation")
        status = None
        if isinstance(evaluation, dict):
            status = evaluation.get("status")
        if status not in {"passed", "failed"}:
            status = payload.get("status")
        if status not in {"passed", "failed"}:
            continue
        bucket = by_module.setdefault(module, {"passed": 0, "failed": 0})
        bucket[status] += 1

        response = payload.get("response")
        if isinstance(response, dict):
            model = response.get("model")
            if isinstance(model, str) and model:
                models[model] += 1

        attempts = payload.get("attempts")
        if isinstance(attempts, list):
            proof_attempts = [attempt for attempt in attempts if isinstance(attempt, dict) and attempt_has_candidate_state(attempt)]
            retry_histogram[len(attempts)] += 1
            if status == "passed" and len(proof_attempts) > 1:
                solved_after_retry += 1
            for attempt in attempts:
                trace = attempt.get("trace")
                if not isinstance(trace, dict):
                    continue
                if int(trace.get("provider_reasoning_chars") or 0) > 0:
                    reasoning_attempts += 1
                if trace.get("candidate_changed_from_previous") is True:
                    candidate_changes += 1
                if trace.get("failure_mode_changed_from_previous") is True:
                    failure_mode_changes += 1

        if status == "failed":
            failure_modes[classify_failure(payload)] += 1

    print(f"artifacts: {artifact_dir}")
    print(f"completed: {len(files)} passed={sum(v['passed'] for v in by_module.values())} failed={sum(v['failed'] for v in by_module.values())}")
    print("by_module:")
    for module, counts in by_module.items():
        print(f"  {module}: {counts['passed']} passed / {counts['failed']} failed")
    if failure_modes:
        print("failure_modes:")
        for label, count in failure_modes.most_common():
            print(f"  {label}: {count}")
    if retry_histogram:
        print("attempt_histogram:")
        for attempt_count, count in sorted(retry_histogram.items()):
            print(f"  {attempt_count} attempts: {count} tasks")
        print("retry_productivity:")
        print(f"  solved_after_retry: {solved_after_retry}")
        print(f"  candidate_changes: {candidate_changes}")
        print(f"  failure_mode_changes: {failure_mode_changes}")
        print(f"  attempts_with_provider_reasoning: {reasoning_attempts}")
    if models:
        print("response_models:")
        for model, count in models.most_common():
            print(f"  {model}: {count}")


def show_attempts(path: Path, limit: int) -> None:
    payload = load_json(path)
    attempts = payload.get("attempts")
    if not isinstance(attempts, list):
        print(f"{path}: no attempts recorded")
        return
    print(f"artifact: {path}")
    print(f"attempts: {len(attempts)}")
    for attempt in attempts[:limit]:
        response = attempt.get("response")
        model = response.get("model") if isinstance(response, dict) else None
        usage = response.get("usage") if isinstance(response, dict) else None
        evaluation = attempt.get("evaluation") if isinstance(attempt.get("evaluation"), dict) else {}
        trace = attempt.get("trace") if isinstance(attempt.get("trace"), dict) else {}
        response_text = attempt.get("response_text")
        response_head = response_text[:240].replace("\n", " ") if isinstance(response_text, str) else ""
        raw_text = attempt.get("response_text_raw")
        raw_head = raw_text[:240].replace("\n", " ") if isinstance(raw_text, str) else ""
        reasoning = attempt.get("provider_reasoning_text")
        reasoning_head = reasoning[:240].replace("\n", " ") if isinstance(reasoning, str) else ""
        details = evaluation.get("details")
        details_head = details[:240].replace("\n", " ") if isinstance(details, str) else ""
        print(
            "  attempt "
            f"{attempt.get('attempt')}: status={evaluation.get('status')} "
            f"failure_mode={evaluation.get('failure_mode')} model={model} "
            f"finish_reason={trace.get('finish_reason')} latency={trace.get('latency_seconds')}"
        )
        if usage:
            print(f"    usage={usage}")
        if trace:
            print(
                "    trace="
                f"candidate_changed={trace.get('candidate_changed_from_previous')} "
                f"failure_mode_changed={trace.get('failure_mode_changed_from_previous')} "
                f"reasoning_chars={trace.get('provider_reasoning_chars')}"
            )
        if response_head:
            print(f"    response_head={response_head}")
        if raw_head and raw_head != response_head:
            print(f"    response_raw_head={raw_head}")
        if reasoning_head:
            print(f"    reasoning_head={reasoning_head}")
        if details_head:
            print(f"    checker_head={details_head}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze benchmark result artifacts.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    summary_parser = subparsers.add_parser("summary", help="Summarize a completed summary JSON file.")
    summary_parser.add_argument("summary_path", type=Path)

    partial_parser = subparsers.add_parser("artifacts", help="Summarize a live artifact directory.")
    partial_parser.add_argument("artifact_dir", type=Path)

    attempts_parser = subparsers.add_parser("attempts", help="Show recorded attempts for one task artifact.")
    attempts_parser.add_argument("artifact_path", type=Path)
    attempts_parser.add_argument("--limit", type=int, default=5)

    args = parser.parse_args()
    if args.command == "summary":
        summarize_summary_file(args.summary_path)
    elif args.command == "artifacts":
        summarize_artifact_dir(args.artifact_dir)
    else:
        show_attempts(args.artifact_path, args.limit)


if __name__ == "__main__":
    main()
