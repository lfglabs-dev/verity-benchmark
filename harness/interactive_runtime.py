from __future__ import annotations

import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from task_runner import ROOT, run_command as lean_run_command

PLACEHOLDER_PATTERN = re.compile(r"\b(sorry|admit|axiom)\b")
HOLE_PATTERN = re.compile(r"\?(?:_|\w+)")
DEF_PATTERN = re.compile(r"^\s*(?:def|theorem|lemma|abbrev|opaque)\s+([A-Za-z0-9_'.]+)")
HIDDEN_PROOF_IMPORT_PATTERN = re.compile(r"^\s*import\s+Benchmark\.Cases\..*\.Proofs\b", re.MULTILINE)
IMPORT_PATTERN = re.compile(r"^\s*import\s+([A-Za-z0-9_.']+)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class RuntimePaths:
    editable_rel_path: str
    theorem_name: str
    implementation_files: tuple[str, ...]
    specification_files: tuple[str, ...]
    public_files: tuple[str, ...]


class TaskProofRuntime:
    def __init__(self, task: dict[str, Any]) -> None:
        editable_files = [str(item) for item in task["editable_files"]]
        if len(editable_files) != 1:
            raise ValueError("tasks must declare exactly one editable Lean file")
        editable_rel_path = editable_files[0]
        self.paths = RuntimePaths(
            editable_rel_path=editable_rel_path,
            theorem_name=str(task["theorem_name"]),
            implementation_files=tuple(str(item) for item in task["implementation_files"]),
            specification_files=tuple(str(item) for item in task["specification_files"]),
            public_files=tuple(
                str(item)
                for item in [
                    *task["implementation_files"],
                    *task["specification_files"],
                    *editable_files,
                ]
            ),
        )
        self.current_proof_text = self._read_repo_file(editable_rel_path)
        self.expected_theorem_signature = self._extract_theorem_signature(self.current_proof_text)
        self.allowed_task_modules = frozenset(self._module_name(path) for path in self.paths.public_files)

    def _read_repo_file(self, rel_path: str) -> str:
        path = ROOT / rel_path
        if not path.is_file():
            raise FileNotFoundError(rel_path)
        return path.read_text(encoding="utf-8")

    def read_public_file(self, rel_path: str) -> dict[str, Any]:
        if rel_path not in self.paths.public_files:
            return {
                "status": "rejected",
                "reason": "path_not_public_for_task",
                "allowed_files": list(self.paths.public_files),
            }
        if rel_path == self.paths.editable_rel_path:
            return {"status": "ok", "path": rel_path, "content": self.current_proof_text}
        try:
            return {"status": "ok", "path": rel_path, "content": self._read_repo_file(rel_path)}
        except FileNotFoundError:
            return {"status": "missing", "path": rel_path}

    def write_editable_proof(self, content: str) -> dict[str, Any]:
        self.current_proof_text = content if content.endswith("\n") else f"{content}\n"
        return {
            "status": "ok",
            "path": self.paths.editable_rel_path,
            "bytes": len(self.current_proof_text.encode("utf-8")),
            "lines": len(self.current_proof_text.splitlines()),
        }

    def search_public_defs(self, query: str, *, limit: int = 20) -> dict[str, Any]:
        query_text = query.strip()
        if not query_text:
            return {"status": "rejected", "reason": "query_must_not_be_empty"}
        lowered = query_text.lower()
        matches: list[dict[str, Any]] = []
        for rel_path in self.paths.implementation_files + self.paths.specification_files:
            path = ROOT / rel_path
            if not path.is_file():
                continue
            for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                name_match = DEF_PATTERN.match(line)
                if not name_match:
                    continue
                def_name = name_match.group(1)
                if lowered not in def_name.lower() and lowered not in line.lower():
                    continue
                matches.append(
                    {
                        "path": rel_path,
                        "line": line_no,
                        "name": def_name,
                        "declaration": line.strip(),
                    }
                )
                if len(matches) >= limit:
                    return {"status": "ok", "query": query_text, "matches": matches, "truncated": True}
        return {"status": "ok", "query": query_text, "matches": matches, "truncated": False}

    def inspect_goals(self) -> dict[str, Any]:
        holes = sorted(set(HOLE_PATTERN.findall(self.current_proof_text)))
        if not holes:
            return {
                "status": "unsupported",
                "reason": "goal_inspection_requires_explicit_hole",
                "details": "Write the proof with a `?_` or named hole first, then retry goal inspection.",
            }
        evaluation = self.evaluate_current(check_goals=True)
        return {
            "status": "ok" if evaluation["status"] == "failed" else "passed",
            "holes": holes,
            "details": evaluation["details"],
            "command": evaluation.get("command"),
        }

    def evaluate_current(self, *, check_goals: bool = False) -> dict[str, Any]:
        return self.evaluate_candidate(self.current_proof_text, check_goals=check_goals)

    def preflight_candidate(self, candidate_text: str) -> dict[str, Any] | None:
        """Fast local checks that don't require running Lean. Returns a failure dict or None if OK."""
        if not candidate_text.strip():
            return {
                "status": "failed",
                "failure_mode": "empty_response",
                "details": "agent response was empty",
            }

        if PLACEHOLDER_PATTERN.search(candidate_text):
            return {
                "status": "failed",
                "failure_mode": "placeholder_detected",
                "details": "candidate proof contains a rejected placeholder token",
            }

        if HIDDEN_PROOF_IMPORT_PATTERN.search(candidate_text):
            return {
                "status": "failed",
                "failure_mode": "hidden_proof_import_detected",
                "details": "candidate proof imports hidden Benchmark.Cases.*.Proofs modules",
            }

        blocked_imports = self._find_blocked_case_imports(candidate_text)
        if blocked_imports:
            return {
                "status": "failed",
                "failure_mode": "hidden_case_import_detected",
                "details": (
                    "candidate proof imports non-public Benchmark.Cases modules: "
                    + ", ".join(blocked_imports)
                ),
            }

        candidate_signature = self._extract_theorem_signature(candidate_text)
        if candidate_signature != self.expected_theorem_signature:
            return {
                "status": "failed",
                "failure_mode": "theorem_statement_mismatch",
                "details": "candidate proof changed the editable theorem statement",
            }

        return None

    def evaluate_candidate(self, candidate_text: str, *, check_goals: bool = False) -> dict[str, Any]:
        preflight_failure = self.preflight_candidate(candidate_text)
        if preflight_failure is not None:
            return preflight_failure

        with tempfile.TemporaryDirectory(prefix="verity-benchmark-agent-") as tmp_dir:
            workspace = Path(tmp_dir) / "workspace"
            self._materialize_workspace(workspace)
            editable_path = workspace / self.paths.editable_rel_path
            editable_path.parent.mkdir(parents=True, exist_ok=True)
            editable_path.write_text(candidate_text, encoding="utf-8")

            if check_goals:
                check_path = editable_path
                command = ["lake", "env", "lean", "--root=.", str(check_path.relative_to(workspace))]
            else:
                check_path = workspace / "CandidateCheck.lean"
                check_path.write_text(
                    candidate_text.rstrip() + f"\n\n#check {self.paths.theorem_name}\n",
                    encoding="utf-8",
                )
                command = ["lake", "env", "lean", "--root=.", str(check_path.relative_to(workspace))]
            code, output = lean_run_command(command, cwd=workspace)
            if code != 0:
                return {
                    "status": "failed",
                    "failure_mode": "lean_check_failed",
                    "details": output,
                    "command": command,
                    "candidate_workspace": str(editable_path.relative_to(workspace)),
                }
            return {
                "status": "passed",
                "failure_mode": None,
                "details": output,
                "command": command,
                "candidate_workspace": str(editable_path.relative_to(workspace)),
            }

    def tool_specs(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "read_public_file",
                    "description": "Read one task-scoped public Lean file from implementation_files, specification_files, or the editable proof.",
                    "parameters": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["path"],
                        "properties": {
                            "path": {
                                "type": "string",
                                "enum": list(self.paths.public_files),
                            }
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "write_editable_proof",
                    "description": "Replace the entire editable proof file with complete Lean code.",
                    "parameters": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["content"],
                        "properties": {
                            "content": {
                                "type": "string",
                            }
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "run_lean_check",
                    "description": "Run the official harness Lean check for the current editable proof.",
                    "parameters": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {},
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "inspect_lean_goals",
                    "description": "Inspect current Lean diagnostics for explicit proof holes in the editable file. Returns unsupported if no hole is present.",
                    "parameters": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {},
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "search_public_defs",
                    "description": "Search public implementation/specification files for matching def/theorem/lemma names.",
                    "parameters": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["query"],
                        "properties": {
                            "query": {"type": "string"},
                            "limit": {"type": "integer", "minimum": 1, "maximum": 50},
                        },
                    },
                },
            },
        ]

    def execute_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name == "read_public_file":
            return self.read_public_file(str(arguments.get("path", "")))
        if name == "write_editable_proof":
            return self.write_editable_proof(str(arguments.get("content", "")))
        if name == "run_lean_check":
            result = self.evaluate_current()
            if result.get("failure_mode") == "lean_check_failed":
                guidance = _build_repair_guidance(str(result.get("details", "")))
                if guidance:
                    result["repair_hints"] = guidance
            return result
        if name == "inspect_lean_goals":
            return self.inspect_goals()
        if name == "search_public_defs":
            limit = int(arguments.get("limit", 20))
            return self.search_public_defs(str(arguments.get("query", "")), limit=limit)
        return {"status": "rejected", "reason": "unknown_tool", "tool": name}

    def _materialize_workspace(self, workspace: Path) -> None:
        workspace.mkdir(parents=True, exist_ok=True)
        for rel_path in (
            "lakefile.lean",
            "lake-manifest.json",
            "lean-toolchain",
            ".lake",
        ):
            source = ROOT / rel_path
            target = workspace / rel_path
            if not source.exists():
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            os.symlink(source, target, target_is_directory=source.is_dir())
        for rel_path in self.paths.public_files:
            source = ROOT / rel_path
            target = workspace / rel_path
            target.parent.mkdir(parents=True, exist_ok=True)
            if rel_path == self.paths.editable_rel_path:
                target.write_text(self.current_proof_text, encoding="utf-8")
                continue
            if not source.is_file():
                continue
            os.symlink(source, target)

    def _extract_theorem_signature(self, text: str) -> str | None:
        short_name = self.paths.theorem_name.rsplit(".", 1)[-1]
        pattern = re.compile(
            rf"theorem\s+{re.escape(short_name)}\b(?P<signature>.*?)(?::=)",
            re.DOTALL,
        )
        match = pattern.search(text)
        if not match:
            return None
        signature = re.sub(r"/-.*?-/", " ", match.group("signature"), flags=re.DOTALL)
        signature = re.sub(r"--.*$", " ", signature, flags=re.MULTILINE)
        return " ".join(signature.split())

    def _find_blocked_case_imports(self, text: str) -> list[str]:
        blocked: list[str] = []
        for module_name in IMPORT_PATTERN.findall(text):
            if not module_name.startswith("Benchmark.Cases."):
                continue
            if module_name in self.allowed_task_modules:
                continue
            blocked.append(module_name)
        return sorted(set(blocked))

    @staticmethod
    def _module_name(rel_path: str) -> str:
        path = Path(rel_path)
        suffix = "".join(path.suffixes)
        module_path = str(path)
        if suffix:
            module_path = module_path[: -len(suffix)]
        return module_path.replace("/", ".")


def _build_repair_guidance(details: str) -> str:
    hints: list[str] = []
    if "tactic 'split' failed" in details:
        hints.append(
            "- Do not `split` the final post-state blindly. Prove branch-specific helper theorems first, then use `by_cases` plus `simpa`."
        )
    if "no goals to be solved" in details:
        hints.append(
            "- A previous `simp` likely closed the goal already. Remove trailing tactics after the goal is solved."
        )
    if "expected type must not contain free variables" in details:
        hints.append(
            "- Do not use `native_decide` or `decide` on goals that still contain parameters. First reduce to concrete equalities."
        )
    if "unknown constant" in details or "Unknown identifier" in details or "unknown identifier" in details:
        hints.append(
            "- You are referencing a lemma or constant that does not exist in this Lean 4 environment. "
            "Do not guess lemma names. Instead, use `simp` with the relevant definitions, `omega` for arithmetic, "
            "or `decide`/`native_decide` for decidable propositions. Remove all references to unknown names."
        )
    if "unsolved goals" in details and "match" in details:
        hints.append(
            "- The remaining goal contains a `match` expression. Use `split` to case-split on the match, "
            "then solve each branch separately. If the match is on a ContractResult, try "
            "`simp only [...]` to reduce it first, or use `cases` on the matched expression."
        )
    if "unsolved goals" in details and "if " in details:
        hints.append(
            "- The remaining goal contains an `if` expression. Use `by_cases h : <condition>` to split on the condition, "
            "then `simp [h, ...]` in each branch. Alternatively, add the condition's hypothesis to the `simp` call."
        )
    if "unsolved goals" in details and "match" not in details and "if " not in details:
        hints.append(
            "- Unsolved goals remain. Check that `simp` is given all necessary definitions and hypotheses."
        )
    if "type mismatch" in details:
        hints.append(
            "- A type mismatch often means the proof term or tactic result does not match the goal. Re-read the spec and ensure your proof targets the correct type."
        )
    if "simp made no progress" in details:
        hints.append(
            "- `simp` made no progress with the given arguments. Add more definitions to unfold, "
            "or the simp arguments may already be fully reduced. Try removing the unproductive simp call."
        )
    if "failed to infer binder type" in details:
        hints.append(
            "- Lean cannot infer a binder type. Add explicit type annotations to your helper lemma parameters."
        )
    if "unexpected token" in details or "expected 'by'" in details:
        hints.append(
            "- Syntax error. Ensure the theorem body uses `:= by` followed by tactics. "
            "Do not use `:=` with a term-mode proof unless you are certain of the syntax."
        )
    if "Function expected at" in details or "unknown identifier" in details:
        hints.append(
            "- Use `s.storage 0` (function application) not `s.storage[0]` or `s.storage.0`. "
            "ContractState.storage is a function `Nat → Uint256`."
        )
    return "\n".join(hints)


def tool_result_json(result: dict[str, Any]) -> str:
    return json.dumps(result, indent=2, sort_keys=True)
