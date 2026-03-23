from __future__ import annotations

import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from task_runner import ROOT, run_command as lean_run_command

# Optional: PyPantograph for structured tactic execution
try:
    import pantograph  # type: ignore[import-untyped]
    PANTOGRAPH_AVAILABLE = True
except ImportError:
    PANTOGRAPH_AVAILABLE = False

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

    def try_tactic_at_hole(self, tactic: str) -> dict[str, Any]:
        """Try replacing all ?_ holes with a specific tactic and check if it works.

        This is a lightweight alternative to PyPantograph for targeted tactic execution.
        The original proof is preserved if the tactic fails.
        """
        if not tactic.strip():
            return {"status": "rejected", "reason": "tactic_must_not_be_empty"}
        original = self.current_proof_text
        # Replace all ?_ holes with the given tactic
        modified = re.sub(r"\?_", tactic.strip(), original)
        if modified == original:
            return {
                "status": "unsupported",
                "reason": "no_holes_found",
                "details": "No `?_` holes in the current proof. Write a proof with `?_` holes first.",
            }
        evaluation = self.evaluate_candidate(modified)
        if evaluation.get("status") == "passed":
            self.current_proof_text = modified
            return {
                "status": "passed",
                "tactic": tactic.strip(),
                "details": "Tactic succeeded. Proof updated.",
            }
        return {
            "status": "failed",
            "tactic": tactic.strip(),
            "details": evaluation.get("details", "")[:2000],
            "failure_class": _classify_failure(str(evaluation.get("details", ""))),
        }

    def evaluate_current(self, *, check_goals: bool = False) -> dict[str, Any]:
        return self.evaluate_candidate(self.current_proof_text, check_goals=check_goals)

    def evaluate_candidate(self, candidate_text: str, *, check_goals: bool = False) -> dict[str, Any]:
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
            {
                "type": "function",
                "function": {
                    "name": "try_tactic_at_hole",
                    "description": "Try replacing all `?_` holes in the current proof with a specific tactic and check if it compiles. Preserves the original proof if it fails. Useful for testing tactics like `simp_all [...]`, `omega`, `decide`, or `duper [...]`.",
                    "parameters": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["tactic"],
                        "properties": {
                            "tactic": {
                                "type": "string",
                                "description": "The Lean tactic to try at each ?_ hole.",
                            }
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
            if result.get("status") == "failed":
                result = self._annotate_check_result(result)
            return result
        if name == "inspect_lean_goals":
            return self.inspect_goals()
        if name == "search_public_defs":
            limit = int(arguments.get("limit", 20))
            return self.search_public_defs(str(arguments.get("query", "")), limit=limit)
        if name == "try_tactic_at_hole":
            return self.try_tactic_at_hole(str(arguments.get("tactic", "")))
        return {"status": "rejected", "reason": "unknown_tool", "tool": name}

    def _annotate_check_result(self, result: dict[str, Any]) -> dict[str, Any]:
        """Annotate a failed check result with failure classification and repair hints."""
        details = str(result.get("details", ""))
        failure_class = _classify_failure(details)
        hints = _build_check_hints(failure_class, details)
        annotated = dict(result)
        annotated["failure_class"] = failure_class
        if hints:
            annotated["repair_hints"] = hints

        # Add structured error summary
        error_lines: list[int] = []
        for match in re.finditer(r":(\d+):\d+: error:", details):
            error_lines.append(int(match.group(1)))
        if error_lines:
            annotated["error_count"] = len(error_lines)
            annotated["first_error_line"] = min(error_lines)

        return annotated

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


def _classify_failure(details: str) -> str:
    """Classify a Lean checker failure into a coarse category."""
    if not details:
        return "unknown"
    lower = details.lower()
    if "unknown identifier" in lower or "unknown constant" in lower:
        return "unknown_identifier"
    if "unsolved goals" in lower:
        return "unsolved_goals"
    if "type mismatch" in lower:
        return "type_mismatch"
    if "tactic 'split' failed" in details:
        return "split_failed"
    if "no goals to be solved" in details:
        return "no_goals"
    if "expected type must not contain free variables" in details:
        return "free_variables"
    if "unknown tactic" in lower:
        return "unknown_tactic"
    if "function expected" in lower or "application type mismatch" in lower:
        return "type_error"
    if "simp made no progress" in lower:
        return "simp_no_progress"
    if "failed to unfold" in lower or "unfold" in lower and "failed" in lower:
        return "unfold_failed"
    if "dsimp made no progress" in lower:
        return "simp_no_progress"
    if "tactic 'rfl' failed" in details:
        return "rfl_failed"
    if "invalid" in lower and "conv tactic" in lower:
        return "tactic_misuse"
    return "other"


def _build_check_hints(failure_class: str, details: str) -> list[str]:
    """Build targeted repair hints based on failure classification."""
    hints: list[str] = []
    if failure_class == "unknown_identifier":
        if "decide_True" in details or "decide_False" in details:
            hints.append("CRITICAL: `decide_True` and `decide_False` do not exist. Remove them. Instead, pass precondition hypotheses directly to `simp` - it handles `decide` reduction automatically.")
        else:
            hints.append("Use search_public_defs to find correct names from spec/impl files.")
        hints.append("Check imports. Standard names: Nat.lt_of_not_ge, Nat.not_le_of_lt.")
    elif failure_class == "unsolved_goals":
        hints.append("Use inspect_lean_goals with a ?_ hole to see exact goal state.")
        if "if " in details or "match" in details:
            hints.append("If simp leaves `if`/`match` with free variables, use `by_cases` on each unresolved condition BEFORE calling simp. Pass all case hypotheses to simp. Do NOT use `split` after simp or `native_decide`/`decide` on goals with free variables.")
        if "unused" in details.lower() and ("hBound" in details or "hypothesis" in details.lower()):
            hints.append("If a hypothesis is reported as unused by simp, try `simp_all` instead of `simp`. `simp_all` rewrites hypotheses into the goal, resolving mismatches between spec helper names and unfolded definitions.")
        hints.append("Try restructuring: `by_cases h : condition · simp [..., h] · simp [..., h]`.")
    elif failure_class == "type_mismatch":
        if "decide" in details:
            hints.append("The goal contains `decide` expressions. Pass all precondition hypotheses to `simp` and it will reduce `decide` automatically. Do NOT try to manually match `decide` types.")
        hints.append("Unfold definitions to align types. Check spec matches impl.")
    elif failure_class == "split_failed":
        hints.append("Do not split the post-state. Use by_cases with branch-specific helpers.")
    elif failure_class == "no_goals":
        hints.append("Previous simp closed the goal. Remove trailing tactics.")
    elif failure_class == "free_variables":
        hints.append("Reduce to concrete equalities before decide/native_decide.")
    elif failure_class == "unknown_tactic":
        hints.append("Use standard Lean 4 / Mathlib tactics only.")
    elif failure_class == "simp_no_progress":
        hints.append("simp/dsimp made no progress. CRITICAL: In each `by_cases` branch, you MUST repeat the FULL simp set (all contract definitions, storage fields, getStorage, setStorage, Verity.require, Verity.bind, Bind.bind, Verity.pure, Pure.pure, Contract.run, ContractResult.snd) PLUS the case hypothesis and all preconditions. Bare `simp [h]` will never work.")
        hints.append("Check that you are using the correct function name from the implementation file.")
    elif failure_class == "unfold_failed":
        hints.append("unfold failed. The definition name may be wrong or not unfoldable.")
        hints.append("Use search_public_defs to find the exact definition name.")
    elif failure_class == "rfl_failed":
        hints.append("rfl failed because the LHS is not definitionally equal to the RHS.")
        if "match" in details or "if " in details:
            hints.append("The goal has unresolved `if`/`match` expressions with free variables. Use `by_cases` on each condition BEFORE calling simp, not `split` after. Pass all case hypotheses to simp. For nested conditionals, nest `by_cases`. Example: `by_cases h : cond; · simp [..., h]; · simp [..., h]`.")
        else:
            hints.append("Try replacing `rfl` with `simp` or adding more definitions to the simp set.")
    elif failure_class == "tactic_misuse":
        hints.append("The tactic was used incorrectly for this goal shape.")
        hints.append("Check the goal state with inspect_lean_goals using a ?_ hole.")
    return hints


def tool_result_json(result: dict[str, Any]) -> str:
    return json.dumps(result, indent=2, sort_keys=True)
