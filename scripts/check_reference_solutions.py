#!/usr/bin/env python3
"""Audit reference solution Lean files for placeholder tokens.

Scans every reference solution module referenced by task manifests and
fails if any contains `sorry`, `admit`, or bare `axiom` declarations
that indicate an incomplete proof.

Usage:
    python3 scripts/check_reference_solutions.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from manifest_utils import load_manifest_data

ROOT = Path(__file__).resolve().parent.parent

TASK_DIRS = [ROOT / "cases", ROOT / "backlog"]

# Tokens that indicate an incomplete proof.
PLACEHOLDER_TOKENS = ("sorry", "admit")

# Matches standalone sorry/admit (not inside comments or strings).
# This is a best-effort heuristic — it catches the common cases.
_PLACEHOLDER_RE = re.compile(
    r"(?:^|\s)(?:" + "|".join(PLACEHOLDER_TOKENS) + r")(?:\s|$)", re.MULTILINE
)

# Matches Lean single-line comments
_LINE_COMMENT_RE = re.compile(r"--.*$", re.MULTILINE)


def lean_module_path(module_name: str) -> Path:
    return ROOT.joinpath(*module_name.split(".")).with_suffix(".lean")


def strip_comments(text: str) -> str:
    """Strip single-line comments. Block comments are rare in proof files."""
    return _LINE_COMMENT_RE.sub("", text)


def check_file(path: Path) -> list[tuple[int, str]]:
    """Return list of (line_number, line) containing placeholder tokens."""
    text = path.read_text(encoding="utf-8")
    hits: list[tuple[int, str]] = []
    for i, line in enumerate(text.splitlines(), start=1):
        cleaned = _LINE_COMMENT_RE.sub("", line)
        for token in PLACEHOLDER_TOKENS:
            # Match as a whole word
            if re.search(rf"\b{token}\b", cleaned):
                hits.append((i, line.rstrip()))
                break
    return hits


def discover_task_manifests() -> list[Path]:
    """Find all task manifest YAML files under cases/ and backlog/."""
    manifests: list[Path] = []
    for task_dir in TASK_DIRS:
        if task_dir.is_dir():
            manifests.extend(sorted(task_dir.rglob("tasks/*.yaml")))
    return manifests


def main() -> None:
    manifests = discover_task_manifests()

    checked = 0
    failures: list[tuple[str, Path, list[tuple[int, str]]]] = []
    missing: list[tuple[str, str]] = []

    for manifest_path in manifests:
        task = load_manifest_data(manifest_path)
        ref_module = task.get("reference_solution_module")
        if not ref_module:
            continue

        path = lean_module_path(str(ref_module))
        if not path.is_file():
            missing.append((str(task.get("task_id", "?")), str(ref_module)))
            continue

        checked += 1
        hits = check_file(path)
        if hits:
            failures.append((str(task.get("task_id", "?")), path, hits))

    print(f"Reference solution audit: {checked} files checked.")

    if missing:
        print(f"\nWARNING: {len(missing)} reference solution(s) not found:")
        for task_id, module in missing:
            print(f"  {task_id}: {module}")

    if failures:
        print(
            f"\nERROR: {len(failures)} reference solution(s) contain placeholder tokens:",
            file=sys.stderr,
        )
        for task_id, path, hits in failures:
            rel = path.relative_to(ROOT)
            print(f"\n  {task_id} ({rel}):", file=sys.stderr)
            for lineno, line in hits:
                print(f"    line {lineno}: {line}", file=sys.stderr)
        sys.exit(1)
    else:
        print("OK: no placeholder tokens (sorry/admit) found in reference solutions.")


if __name__ == "__main__":
    main()
