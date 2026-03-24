#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error, request

from benchmark_config import load_benchmark_agent_defaults
from interactive_runtime import TaskProofRuntime, tool_result_json
from task_runner import ROOT, load_task_record, resolve_task_manifest

AGENT_RESULTS_DIR = ROOT / "results" / "agent_runs"
SCHEMA_PATH = ROOT / "schemas" / "agent-config.schema.json"
RUN_SCHEMA_PATH = ROOT / "schemas" / "agent-run.schema.json"
BENCHMARK_DEFAULTS = load_benchmark_agent_defaults()
DEFAULT_PROFILE = BENCHMARK_DEFAULTS.default_agent_default_profile
AGENT_PROFILES_DIR = ROOT / BENCHMARK_DEFAULTS.default_agent_profiles_dir
DEFAULT_AGENT_CONFIG_PATH = ROOT / BENCHMARK_DEFAULTS.default_agent_config
PLACEHOLDER_PATTERN = re.compile(r"\b(sorry|admit|axiom)\b")
MAX_ERROR_FEEDBACK_CHARS = 6000
MAX_REASONING_SNIPPET_CHARS = 4000
ADAPTER_PROTOCOL_VERSION = 1
THINK_BLOCK_PATTERN = re.compile(r"(?s)<think>(.*?)</think>\s*")


@dataclass(frozen=True)
class ResolvedAgentConfig:
    profile: str | None
    agent_id: str
    track: str
    run_slug: str
    adapter: str
    config_path: str
    base_url: str
    base_url_env: str | None
    model: str
    model_env: str | None
    api_key: str
    api_key_env: str | None
    chat_completions_path: str
    models_path: str
    system_prompt_files: list[str]
    mode: str
    temperature: float
    max_completion_tokens: int
    max_attempts: int
    max_tool_calls: int
    headers: dict[str, str]
    header_envs: dict[str, str]
    env_contract: dict[str, list[str]]
    extra_body: dict[str, Any]
    request_timeout_seconds: int
    command: list[str]


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def type_matches(value: object, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    raise ValueError(f"unsupported schema type {expected!r}")


def validate(value: object, schema: dict[str, Any], path: str) -> list[str]:
    errors: list[str] = []

    schema_type = schema.get("type")
    if schema_type is not None:
        if isinstance(schema_type, list):
            if not any(type_matches(value, item) for item in schema_type):
                errors.append(f"{path}: expected one of {schema_type}, got {type(value).__name__}")
                return errors
        elif not type_matches(value, schema_type):
            errors.append(f"{path}: expected {schema_type}, got {type(value).__name__}")
            return errors

    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: expected constant {schema['const']!r}, got {value!r}")

    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: expected one of {schema['enum']}, got {value!r}")

    if isinstance(value, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                errors.append(f"{path}: missing required key {key!r}")

        properties = schema.get("properties", {})
        additional = schema.get("additionalProperties", True)
        for key, item in value.items():
            if key in properties:
                errors.extend(validate(item, properties[key], f"{path}.{key}"))
            elif additional is False:
                errors.append(f"{path}: unexpected key {key!r}")
            elif isinstance(additional, dict):
                errors.extend(validate(item, additional, f"{path}.{key}"))

    if isinstance(value, list) and "items" in schema:
        for index, item in enumerate(value):
            errors.extend(validate(item, schema["items"], f"{path}[{index}]"))

    if isinstance(value, str):
        min_length = schema.get("minLength")
        if min_length is not None and len(value) < min_length:
            errors.append(f"{path}: expected string length >= {min_length}, got {len(value)}")

    if isinstance(value, list):
        min_items = schema.get("minItems")
        if min_items is not None and len(value) < min_items:
            errors.append(f"{path}: expected at least {min_items} item(s), got {len(value)}")
        if schema.get("uniqueItems"):
            duplicates: list[object] = []
            for item in value:
                if item in duplicates:
                    continue
                if value.count(item) > 1:
                    duplicates.append(item)
            if duplicates:
                errors.append(f"{path}: expected unique items, got duplicates {duplicates!r}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        minimum = schema.get("minimum")
        if minimum is not None and value < minimum:
            errors.append(f"{path}: expected >= {minimum}, got {value}")

    return errors


def validate_config_data(data: object, label: str) -> dict[str, Any]:
    schema = load_json(SCHEMA_PATH)
    if not isinstance(data, dict):
        raise SystemExit(f"{label}: config must decode to an object")
    errors = validate(data, schema, label)
    errors.extend(validate_agent_contract(data, label))
    if errors:
        raise SystemExit("\n".join(errors))
    return data


def load_config(path: Path) -> dict[str, Any]:
    return validate_config_data(load_json(path), config_label(path))


def config_label(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def explicit_config_path(config_path: str) -> Path:
    candidate = Path(config_path)
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    if candidate.is_file():
        return candidate
    raise SystemExit(f"agent config file not found: {config_label(candidate)}")


def profile_path(profile: str) -> Path:
    name = profile.strip()
    if not name:
        raise SystemExit("profile name must not be empty")
    if "/" in name or name.startswith("."):
        raise SystemExit(f"invalid profile name {profile!r}")
    return AGENT_PROFILES_DIR / f"{name}.json"


def resolve_config_path(config_or_profile: str | None, profile: str | None) -> Path:
    if config_or_profile and profile:
        raise SystemExit("pass either --config or --profile, not both")
    if profile:
        path = profile_path(profile)
        if not path.is_file():
            raise SystemExit(f"agent profile not found: {config_label(path)}")
        return path
    if config_or_profile:
        candidate = Path(config_or_profile)
        if not candidate.is_absolute():
            candidate = ROOT / candidate
        if candidate.is_file():
            return candidate
        fallback = profile_path(config_or_profile)
        if fallback.is_file():
            return fallback
        raise SystemExit(
            f"agent config not found: {config_or_profile!r} "
            f"(checked file {config_label(candidate)} and profile {config_label(fallback)})"
        )
    if DEFAULT_AGENT_CONFIG_PATH.is_file():
        return DEFAULT_AGENT_CONFIG_PATH
    default_path = profile_path(DEFAULT_PROFILE)
    if default_path.is_file():
        return default_path
    raise SystemExit(
        "default agent config not found: "
        f"{config_label(DEFAULT_AGENT_CONFIG_PATH)} "
        f"(fallback profile {config_label(default_path)})"
    )


def discover_profiles() -> list[str]:
    if not AGENT_PROFILES_DIR.is_dir():
        return []
    return sorted(path.stem for path in AGENT_PROFILES_DIR.glob("*.json") if path.is_file())


def normalize_string(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def validate_agent_contract(config: dict[str, Any], label: str) -> list[str]:
    errors: list[str] = []
    mode = normalize_string(config.get("mode"))
    adapter = normalize_string(config.get("adapter"))

    for field in ("agent_id", "run_slug"):
        if not normalize_string(config.get(field)):
            errors.append(f"{label}: {field!r} must be a non-empty string")

    if mode not in {"strict", "interactive", "custom"}:
        errors.append(f"{label}: 'mode' must be one of ['strict', 'interactive', 'custom']")

    if adapter == "openai_compatible":
        for field in ("base_url", "model", "api_key"):
            direct_value = normalize_string(config.get(field))
            env_name = normalize_string(config.get(f"{field}_env"))
            if direct_value or env_name:
                continue
            errors.append(f"{label}: set either {field!r} or {field + '_env'!r}")
        for field in ("chat_completions_path", "models_path"):
            value = normalize_string(config.get(field))
            if not value:
                errors.append(f"{label}: {field!r} must be a non-empty string")
            elif not value.startswith("/"):
                errors.append(f"{label}: {field!r} must start with '/' for openai_compatible adapters")
    elif adapter == "command":
        raw_command = config.get("command")
        if not isinstance(raw_command, list) or not raw_command:
            errors.append(f"{label}: 'command' must be a non-empty array for command adapters")
        else:
            for index, item in enumerate(raw_command):
                if not normalize_string(item):
                    errors.append(f"{label}: command[{index}] must be a non-empty string")
            if command_requires_openai_connection(raw_command):
                for field in ("base_url", "model", "api_key"):
                    direct_value = normalize_string(config.get(field))
                    env_name = normalize_string(config.get(f"{field}_env"))
                    if direct_value or env_name:
                        continue
                    errors.append(
                        f"{label}: bundled openai-compatible command adapter requires "
                        f"either {field!r} or {field + '_env'!r}"
                    )
                for field in ("chat_completions_path", "models_path"):
                    value = normalize_string(config.get(field))
                    if not value:
                        errors.append(f"{label}: {field!r} must be a non-empty string")
                    elif not value.startswith("/"):
                        errors.append(f"{label}: {field!r} must start with '/'")
    else:
        errors.append(f"{label}: unsupported adapter {adapter!r}")

    if mode in {"strict", "interactive"} and adapter != "openai_compatible":
        errors.append(f"{label}: mode {mode!r} requires adapter 'openai_compatible'")
    if mode == "custom" and adapter != "command":
        errors.append(f"{label}: mode 'custom' requires adapter 'command'")

    prompt_files = config.get("system_prompt_files", [])
    if isinstance(prompt_files, list):
        for index, item in enumerate(prompt_files):
            if not normalize_string(item):
                errors.append(f"{label}: system_prompt_files[{index}] must be a non-empty string")

    raw_header_envs = config.get("header_envs", {})
    if isinstance(raw_header_envs, dict):
        for header_name, env_name in raw_header_envs.items():
            if not normalize_string(header_name):
                errors.append(f"{label}: header_envs contains a blank header name")
            if not normalize_string(env_name):
                errors.append(f"{label}: header_envs[{header_name!r}] must be a non-empty env var name")

    return errors


def slugify(value: str) -> str:
    slug_chars: list[str] = []
    previous_dash = False
    for char in value.strip().lower():
        if char.isalnum():
            slug_chars.append(char)
            previous_dash = False
            continue
        if not previous_dash:
            slug_chars.append("-")
            previous_dash = True
    slug = "".join(slug_chars).strip("-")
    return slug or "agent"


def resolve_track(config: dict[str, Any], *, profile: str | None) -> str:
    explicit = normalize_string(config.get("track"))
    if explicit:
        return explicit
    if profile == DEFAULT_PROFILE:
        return "reference"
    return "custom"


def resolve_mode(config: dict[str, Any], *, profile: str | None) -> str:
    explicit = normalize_string(config.get("mode"))
    if explicit:
        return explicit
    if profile == DEFAULT_PROFILE:
        return "strict"
    return "custom"


def resolve_run_slug(config: dict[str, Any], *, agent_id: str, profile: str | None) -> str:
    explicit = normalize_string(config.get("run_slug"))
    if explicit:
        return slugify(explicit)
    if profile:
        return slugify(profile)
    return slugify(agent_id)


def resolve_field(config: dict[str, Any], field: str, *, required: bool) -> str | None:
    direct_value = normalize_string(config.get(field))
    if direct_value:
        return direct_value
    env_name = normalize_string(config.get(f"{field}_env"))
    if env_name:
        env_value = normalize_string(os.environ.get(env_name))
        if env_value:
            return env_value
        if required:
            raise SystemExit(f"missing required environment variable {env_name!r} for {field}")
        return None
    if required:
        raise SystemExit(f"missing required config value for {field}")
    return None


def resolve_headers(config: dict[str, Any]) -> dict[str, str]:
    headers: dict[str, str] = {}
    raw_headers = config.get("headers", {})
    if isinstance(raw_headers, dict):
        headers.update({str(key): str(value) for key, value in raw_headers.items()})

    raw_header_envs = config.get("header_envs", {})
    if isinstance(raw_header_envs, dict):
        for header_name, env_name in raw_header_envs.items():
            env_value = normalize_string(os.environ.get(str(env_name)))
            if env_value:
                headers[str(header_name)] = env_value

    return headers


def redact_headers(headers: dict[str, str]) -> dict[str, str]:
    return {str(header_name): "<redacted>" for header_name in headers}


def resolve_command(config: dict[str, Any]) -> list[str]:
    raw_command = config.get("command", [])
    if not isinstance(raw_command, list):
        return []
    return [str(item) for item in raw_command]


def command_requires_openai_connection(command: list[object]) -> bool:
    command_text = " ".join(str(item) for item in command)
    return "openai_compatible_adapter.py" in command_text


def resolve_config(path: Path, *, require_secrets: bool, profile: str | None = None) -> ResolvedAgentConfig:
    config = load_config(path)
    agent_id = str(config["agent_id"])
    adapter = str(config["adapter"])
    mode = resolve_mode(config, profile=profile)
    command = resolve_command(config)
    requires_openai_connection = adapter == "openai_compatible" or command_requires_openai_connection(command)
    prompt_files = [str(item) for item in config["system_prompt_files"]]
    missing_files = [item for item in prompt_files if not (ROOT / item).is_file()]
    if missing_files:
        raise SystemExit(f"missing system prompt files: {', '.join(missing_files)}")

    return ResolvedAgentConfig(
        profile=profile,
        agent_id=agent_id,
        track=resolve_track(config, profile=profile),
        run_slug=resolve_run_slug(config, agent_id=agent_id, profile=profile),
        adapter=adapter,
        config_path=config_label(path),
        base_url=(resolve_field(config, "base_url", required=require_secrets and requires_openai_connection) or "").rstrip("/"),
        base_url_env=normalize_string(config.get("base_url_env")),
        model=resolve_field(config, "model", required=require_secrets and requires_openai_connection) or "",
        model_env=normalize_string(config.get("model_env")),
        api_key=resolve_field(config, "api_key", required=require_secrets and requires_openai_connection) or "",
        api_key_env=normalize_string(config.get("api_key_env")),
        chat_completions_path=str(config.get("chat_completions_path") or ""),
        models_path=str(config.get("models_path") or ""),
        system_prompt_files=prompt_files,
        mode=mode,
        temperature=float(config["temperature"]),
        max_completion_tokens=int(config["max_completion_tokens"]),
        max_attempts=int(config.get("max_attempts", 5)),
        max_tool_calls=int(config.get("max_tool_calls", 24)),
        headers=resolve_headers(config),
        header_envs={str(key): str(value) for key, value in dict(config.get("header_envs", {})).items()},
        env_contract=env_contract(config),
        extra_body=dict(config.get("extra_body", {})),
        request_timeout_seconds=int(config.get("request_timeout_seconds", 120)),
        command=command,
    )


def build_system_prompt(config: ResolvedAgentConfig) -> str:
    sections = []
    for rel_path in config.system_prompt_files:
        path = ROOT / rel_path
        sections.append(f"[{rel_path}]\n{path.read_text(encoding='utf-8').strip()}")
    return "\n\n".join(sections).strip()


def render_file_bundle(paths: list[str]) -> str:
    sections = []
    for rel_path in paths:
        path = ROOT / rel_path
        if not path.is_file():
            sections.append(f"[{rel_path}]\n<missing>")
            continue
        contents = path.read_text(encoding="utf-8").strip()
        lines = [line.strip() for line in contents.splitlines() if line.strip()]
        if len(lines) == 1 and lines[0].startswith("import "):
            continue
        sections.append(f"[{rel_path}]\n{contents}")
    return "\n\n".join(sections).strip()


def build_proof_hints(task: dict[str, Any]) -> str:
    family = str(task.get("proof_family", ""))
    shared = [
        "Verity execution proofs often need `simp` with the operational definitions, not just the theorem spec.",
        "Useful simplification symbols are often: `getStorage`, `setStorage`, `Verity.require`, `Verity.bind`, `Bind.bind`, `Verity.pure`, `Pure.pure`, `Contract.run`, and `ContractResult.snd`.",
        "If `simp` gets stuck on a conditional execution path, prove branch-specific private helper theorems with explicit hypotheses instead of splitting the final post-state directly.",
        "If helpful, add imports required for proof automation, for example `import Verity.Proofs.Stdlib.Automation`.",
    ]
    family_specific: list[str] = []
    if family == "state_preservation_local_effects":
        family_specific = [
            "For local-effect theorems, unfold the spec, split on branch conditions, prove concrete slot-write equalities, then finish with `simpa`.",
        ]
    elif family == "protocol_transition_correctness":
        family_specific = [
            "For transition theorems, use `by_cases` on threshold guards before simplifying the execution trace.",
            "For hypotheses of the form `hSmall : x < c`, the negated branch fact is often `have hNotBranch : ¬ c ≤ x := Nat.not_le_of_lt hSmall`.",
        ]
    elif family == "authorization_enablement":
        family_specific = [
            "For authorization theorems, unfold the spec and simplify the guarded execution path using the permission hypotheses.",
        ]
    elif family == "refinement_equivalence":
        family_specific = [
            "For refinement/equivalence theorems, normalize both sides into the same post-state shape before comparing observables.",
        ]
    elif family == "functional_correctness":
        family_specific = [
            "For functional-correctness theorems, unfold the spec to the mathematical target form before simplifying the execution result.",
        ]
    lines = ["Public proof hints:"] + [f"- {item}" for item in [*shared, *family_specific]]
    return "\n".join(lines)


def build_user_prompt(task: dict[str, Any], *, interactive: bool) -> str:
    editable_file = task["editable_files"][0]
    mode_instructions = (
        "You are in interactive mode.\n"
        "All implementation, specification, and editable proof files are already provided below. "
        "Do NOT re-read them with read_public_file — start working immediately.\n"
        "Workflow: call write_editable_proof with your complete proof file, then call run_lean_check to verify.\n"
        "If the check fails, read the error, fix the proof, and repeat write_editable_proof + run_lean_check.\n"
        "Only use read_public_file or search_public_defs if you need a definition not shown below.\n"
        "Do not ask for or attempt arbitrary shell access, arbitrary filesystem access, or files outside this task.\n"
    ) if interactive else (
        "The harness may give you several bounded repair rounds for the same task.\n"
        "On every round, return the complete editable Lean proof file, not a patch or explanation.\n"
    )
    return (
        "You are running the default benchmark agent for verity-benchmark.\n"
        "Treat this as a strict proof-generation benchmark.\n"
        "Do not invent specs, modify implementations, or rely on hidden reference proofs.\n\n"
        f"{mode_instructions}\n"
        "Do not claim that you will inspect more files or run commands.\n"
        "Reason only from the task payload and the file contents included below.\n"
        "Return Lean code only if you answer with a final proof file.\n"
        f"Task ref: {task['task_ref']}\n"
        f"Theorem name: {task['theorem_name']}\n"
        f"Proof family: {task['proof_family']}\n"
        f"Editable file: {editable_file}\n\n"
        "Implementation file contents:\n"
        f"{render_file_bundle(task['implementation_files'])}\n\n"
        "Specification file contents:\n"
        f"{render_file_bundle(task['specification_files'])}\n\n"
        "Editable proof template contents:\n"
        f"{render_file_bundle(task['editable_files'])}\n\n"
        f"{build_proof_hints(task)}\n"
    )


def build_messages(config: ResolvedAgentConfig, task: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": build_system_prompt(config)},
        {"role": "user", "content": build_user_prompt(task, interactive=config.mode == "interactive")},
    ]


def build_repair_guidance(details: str) -> str:
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


def build_repair_messages(
    base_messages: list[dict[str, Any]],
    candidate_text: str,
    evaluation: dict[str, Any],
    *,
    attempt_index: int,
    max_attempts: int,
) -> list[dict[str, Any]]:
    details = str(evaluation.get("details", "")).strip()
    trimmed_details = details[:MAX_ERROR_FEEDBACK_CHARS]
    guidance = build_repair_guidance(trimmed_details)
    repair_prompt = (
        f"The previous Lean file did not pass the checker (attempt {attempt_index} of {max_attempts}).\n"
        "Return a corrected complete replacement for the editable Lean proof file.\n"
        "Return Lean code only, with no markdown fences or extra explanation.\n\n"
        "Previous candidate file:\n"
        f"{candidate_text.rstrip()}\n\n"
        "Lean checker output:\n"
        f"{trimmed_details}\n"
    )
    if guidance:
        repair_prompt += f"\nGeneric repair guidance:\n{guidance}\n"
    return [
        *base_messages,
        {"role": "assistant", "content": candidate_text},
        {"role": "user", "content": repair_prompt},
    ]


def reasoning_excerpt(response: dict[str, Any]) -> str:
    reasoning = extract_response_content(response)["provider_reasoning_text"]
    return reasoning[:MAX_REASONING_SNIPPET_CHARS]


def response_message(response: dict[str, Any]) -> dict[str, Any]:
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        return {}
    message = choices[0].get("message", {})
    return message if isinstance(message, dict) else {}


def extract_response_content(response: dict[str, Any]) -> dict[str, str]:
    message = response_message(response)
    reasoning_parts: list[str] = []
    reasoning_content = message.get("reasoning_content")
    if isinstance(reasoning_content, str) and reasoning_content.strip():
        reasoning_parts.append(reasoning_content.strip())

    raw_segments: list[str] = []
    content = message.get("content")
    if isinstance(content, str):
        raw_segments.append(content.strip())
        reasoning_parts.extend(match.strip() for match in THINK_BLOCK_PATTERN.findall(content) if match.strip())
    elif isinstance(content, list):
        for item in content:
            if not isinstance(item, dict):
                continue
            item_type = item.get("type")
            text = item.get("text")
            if item_type == "text" and isinstance(text, str):
                raw_segments.append(text.strip())
                reasoning_parts.extend(match.strip() for match in THINK_BLOCK_PATTERN.findall(text) if match.strip())
            elif isinstance(text, str) and item_type in {"reasoning", "thinking"} and text.strip():
                reasoning_parts.append(text.strip())

    raw_text = "\n".join(segment for segment in raw_segments if segment).strip()
    return {
        "response_text_raw": raw_text,
        "response_text": THINK_BLOCK_PATTERN.sub("", raw_text).strip(),
        "provider_reasoning_text": "\n\n".join(part for part in reasoning_parts if part).strip(),
    }


def first_choice(response: dict[str, Any]) -> dict[str, Any]:
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        return {}
    choice = choices[0]
    return choice if isinstance(choice, dict) else {}


def stable_digest(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def prompt_chars(messages: list[dict[str, Any]]) -> int:
    total = 0
    for message in messages:
        content = message.get("content")
        if isinstance(content, str):
            total += len(content)
    return total


def attempt_has_candidate_state(attempt: dict[str, Any] | None) -> bool:
    if not isinstance(attempt, dict):
        return False
    candidate_text = attempt.get("candidate_file_contents")
    if isinstance(candidate_text, str) and candidate_text.strip():
        return True
    evaluation = attempt.get("evaluation")
    if not isinstance(evaluation, dict):
        return False
    status = evaluation.get("status")
    failure_mode = evaluation.get("failure_mode")
    return bool((isinstance(status, str) and status) or (isinstance(failure_mode, str) and failure_mode))


def latest_candidate_attempt(attempts: list[dict[str, Any]]) -> dict[str, Any] | None:
    for attempt in reversed(attempts):
        if attempt_has_candidate_state(attempt):
            return attempt
    return None


def build_attempt_trace(
    *,
    messages: list[dict[str, Any]],
    response: dict[str, Any],
    response_content: dict[str, str],
    candidate_text: str,
    evaluation: dict[str, Any] | None,
    previous_attempt: dict[str, Any] | None,
    latency_seconds: float | None,
) -> dict[str, Any]:
    choice = first_choice(response)
    usage = response.get("usage")
    usage_payload = usage if isinstance(usage, dict) else {}
    previous_trace = previous_attempt.get("trace", {}) if isinstance(previous_attempt, dict) else {}
    previous_candidate = str(previous_attempt.get("candidate_file_contents", "")) if isinstance(previous_attempt, dict) else ""
    failure_mode = evaluation.get("failure_mode") if isinstance(evaluation, dict) else None
    status = evaluation.get("status") if isinstance(evaluation, dict) else None
    return {
        "prompt_message_count": len(messages),
        "prompt_chars": prompt_chars(messages),
        "prompt_sha256": stable_digest(messages),
        "response_model": response.get("model"),
        "finish_reason": choice.get("finish_reason"),
        "usage": usage_payload,
        "latency_seconds": round(latency_seconds, 3) if isinstance(latency_seconds, (int, float)) else None,
        "response_text_chars": len(response_content["response_text"]),
        "response_text_raw_chars": len(response_content["response_text_raw"]),
        "provider_reasoning_chars": len(response_content["provider_reasoning_text"]),
        "candidate_chars": len(candidate_text),
        "candidate_sha256": stable_digest(candidate_text),
        "status": status,
        "failure_mode": failure_mode,
        "candidate_changed_from_previous": None if previous_attempt is None else candidate_text != previous_candidate,
        "failure_mode_changed_from_previous": (
            None if previous_attempt is None else failure_mode != previous_trace.get("failure_mode")
        ),
    }


def build_attempt_record(
    *,
    attempt_index: int,
    mode: str,
    messages: list[dict[str, Any]],
    response: dict[str, Any],
    candidate_text: str,
    evaluation: dict[str, Any] | None,
    previous_attempt: dict[str, Any] | None,
    latency_seconds: float | None,
) -> dict[str, Any]:
    response_content = extract_response_content(response)
    return {
        "attempt": attempt_index,
        "mode": mode,
        "messages": list(messages),
        "response": response,
        "response_text": response_content["response_text"],
        "response_text_raw": response_content["response_text_raw"],
        "provider_reasoning_text": response_content["provider_reasoning_text"],
        "candidate_file_contents": candidate_text,
        "evaluation": evaluation or {},
        "trace": build_attempt_trace(
            messages=list(messages),
            response=response,
            response_content=response_content,
            candidate_text=candidate_text,
            evaluation=evaluation,
            previous_attempt=previous_attempt,
            latency_seconds=latency_seconds,
        ),
    }


def refresh_attempt_record(
    attempt: dict[str, Any],
    *,
    candidate_text: str,
    evaluation: dict[str, Any],
    previous_attempt: dict[str, Any] | None,
    latency_seconds: float | None = None,
) -> None:
    attempt["candidate_file_contents"] = candidate_text
    attempt["evaluation"] = evaluation
    prior_trace = attempt.get("trace")
    attempt["trace"] = build_attempt_trace(
        messages=list(attempt.get("messages", [])),
        response=attempt.get("response", {}) if isinstance(attempt.get("response"), dict) else {},
        response_content={
            "response_text": str(attempt.get("response_text", "")),
            "response_text_raw": str(attempt.get("response_text_raw", "")),
            "provider_reasoning_text": str(attempt.get("provider_reasoning_text", "")),
        },
        candidate_text=candidate_text,
        evaluation=evaluation,
        previous_attempt=previous_attempt,
        latency_seconds=(
            latency_seconds
            if latency_seconds is not None
            else prior_trace.get("latency_seconds")
            if isinstance(prior_trace, dict)
            else None
        ),
    )


def build_run_analysis(
    *,
    attempts: list[dict[str, Any]],
    evaluation: dict[str, Any],
    tool_calls_used: int,
) -> dict[str, Any]:
    reasoning_attempts = 0
    candidate_change_count = 0
    failure_mode_change_count = 0
    for attempt in attempts:
        trace = attempt.get("trace", {})
        if not isinstance(trace, dict):
            continue
        if int(trace.get("provider_reasoning_chars") or 0) > 0:
            reasoning_attempts += 1
        if trace.get("candidate_changed_from_previous") is True:
            candidate_change_count += 1
        if trace.get("failure_mode_changed_from_previous") is True:
            failure_mode_change_count += 1
    return {
        "attempt_count": len(attempts),
        "tool_calls_used": tool_calls_used,
        "reasoning_attempt_count": reasoning_attempts,
        "candidate_change_count": candidate_change_count,
        "failure_mode_change_count": failure_mode_change_count,
        "final_failure_mode": evaluation.get("failure_mode"),
        "final_status": evaluation.get("status"),
    }


def build_finalization_messages(
    base_messages: list[dict[str, Any]],
    response: dict[str, Any],
    *,
    attempt_index: int,
    max_attempts: int,
) -> list[dict[str, Any]]:
    reasoning = reasoning_excerpt(response)
    prompt = (
        f"Your previous reply did not include a final Lean file (attempt {attempt_index} of {max_attempts}).\n"
        "Stop reasoning and return the complete contents of the editable Lean proof file now.\n"
        "Return Lean code only, with no markdown fences or extra explanation.\n"
    )
    if reasoning:
        prompt += f"\nPrevious internal draft excerpt:\n{reasoning}\n"
    return [
        *base_messages,
        {"role": "user", "content": prompt},
    ]


def send_chat_completion(
    config: ResolvedAgentConfig,
    messages: list[dict[str, Any]],
    *,
    tools: list[dict[str, Any]] | None = None,
    max_tokens_override: int | None = None,
) -> dict[str, Any]:
    url = f"{config.base_url}{config.chat_completions_path}"
    payload = {
        "model": config.model,
        "messages": messages,
        "temperature": config.temperature,
        "max_tokens": max_tokens_override or config.max_completion_tokens,
    }
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"
    payload.update(config.extra_body)
    req = request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "verity-benchmark/0.1",
            **config.headers,
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=config.request_timeout_seconds) as response:
            body = response.read().decode("utf-8")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"chat completion request failed with HTTP {exc.code}: {detail}") from exc
    except error.URLError as exc:
        raise SystemExit(f"chat completion request failed: {exc}") from exc
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"chat completion request returned non-JSON response: {body[:400]!r}") from exc


def list_models(config: ResolvedAgentConfig) -> dict[str, Any]:
    url = f"{config.base_url}{config.models_path}"
    headers = {
        "User-Agent": "verity-benchmark/0.1",
        **config.headers,
    }
    if config.api_key:
        headers["Authorization"] = f"Bearer {config.api_key}"
    req = request.Request(url, headers=headers, method="GET")
    try:
        with request.urlopen(req, timeout=config.request_timeout_seconds) as response:
            body = response.read().decode("utf-8")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"model probe failed with HTTP {exc.code}: {detail}") from exc
    except error.URLError as exc:
        raise SystemExit(f"model probe failed: {exc}") from exc
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"model probe returned non-JSON response: {body[:400]!r}") from exc


def extract_model_ids(models_payload: dict[str, Any]) -> list[str]:
    data = models_payload.get("data")
    if not isinstance(data, list):
        return []
    model_ids: list[str] = []
    for item in data:
        if isinstance(item, dict):
                model_id = item.get("id")
                if isinstance(model_id, str):
                    model_ids.append(model_id)
    return model_ids


def ensure_configured_model_available(config: ResolvedAgentConfig, model_ids: list[str]) -> None:
    if not model_ids:
        raise SystemExit(
            "model probe could not confirm configured model "
            f"{config.model!r}: {config.models_path} returned no parseable model ids"
        )
    if config.model not in model_ids:
        raise SystemExit(
            "model probe could not confirm configured model "
            f"{config.model!r}: not present in {config.models_path} response"
        )


def extract_text(response: dict[str, Any]) -> str:
    return extract_response_content(response)["response_text"]


def extract_tool_calls(response: dict[str, Any]) -> list[dict[str, Any]]:
    message = response_message(response)
    tool_calls = message.get("tool_calls")
    if isinstance(tool_calls, list):
        return [item for item in tool_calls if isinstance(item, dict)]
    return []


def extract_candidate_file(response_text: str) -> str:
    text = response_text.strip()
    fenced = re.findall(r"```(?:lean)?\s*\n(.*?)```", text, flags=re.DOTALL)
    if len(fenced) == 1:
        return fenced[0].strip() + "\n"
    return text + ("\n" if text and not text.endswith("\n") else "")


def evaluate_candidate_submission(task: dict[str, Any], candidate_text: str) -> dict[str, Any]:
    try:
        runtime = TaskProofRuntime(task)
    except ValueError as exc:
        return {
            "status": "failed",
            "failure_mode": "editable_file_contract_invalid",
            "details": str(exc),
        }
    return runtime.evaluate_candidate(candidate_text)


def parse_tool_arguments(raw_arguments: object) -> dict[str, Any]:
    if isinstance(raw_arguments, dict):
        return raw_arguments
    if not isinstance(raw_arguments, str):
        return {}
    text = raw_arguments.strip()
    if not text:
        return {}
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def build_task_payload(task: dict[str, Any]) -> dict[str, Any]:
    return {
        "task_ref": task["task_ref"],
        "task_id": task["task_id"],
        "case_id": task["case_id"],
        "track": task["track"],
        "property_class": task["property_class"],
        "category": task["category"],
        "difficulty": task["difficulty"],
        "theorem_name": task["theorem_name"],
        "proof_family": task["proof_family"],
        "implementation_files": task["implementation_files"],
        "specification_files": task["specification_files"],
        "editable_files": task["editable_files"],
        "targets": task["targets"],
        "evaluation": task["evaluation"],
        "readiness": task["readiness"],
        "manifest_path": task["manifest_path"],
        "case_manifest_path": task["case_manifest_path"],
    }


def load_public_task_files(task: dict[str, Any]) -> list[dict[str, str]]:
    rel_paths = [
        *[str(item) for item in task["implementation_files"]],
        *[str(item) for item in task["specification_files"]],
        *[str(item) for item in task["editable_files"]],
    ]
    files: list[dict[str, str]] = []
    for rel_path in rel_paths:
        path = ROOT / rel_path
        files.append(
            {
                "path": rel_path,
                "content": path.read_text(encoding="utf-8") if path.is_file() else "",
            }
        )
    return files


def build_command_adapter_request(
    config: ResolvedAgentConfig,
    task: dict[str, Any],
    messages: list[dict[str, Any]],
    *,
    kind: str,
) -> dict[str, Any]:
    return {
        "protocol_version": ADAPTER_PROTOCOL_VERSION,
        "kind": kind,
        "mode": config.mode,
        "task_ref": task["task_ref"],
        "task": build_task_payload(task),
        "public_files": load_public_task_files(task),
        "editable_file": task["editable_files"][0] if task["editable_files"] else None,
        "input": {
            "messages": messages,
            "system_prompt": messages[0]["content"] if messages else "",
            "user_prompt": messages[1]["content"] if len(messages) > 1 else "",
        },
        "agent": {
            "agent_id": config.agent_id,
            "mode": config.mode,
            "track": config.track,
            "run_slug": config.run_slug,
            "adapter": config.adapter,
            "config_path": config.config_path,
            "base_url": config.base_url or None,
            "model": config.model or None,
            "api_key": config.api_key or None,
            "chat_completions_path": config.chat_completions_path or None,
            "models_path": config.models_path or None,
            "temperature": config.temperature,
            "max_completion_tokens": config.max_completion_tokens,
            "max_attempts": config.max_attempts,
            "max_tool_calls": config.max_tool_calls,
            "headers": config.headers,
            "extra_body": config.extra_body,
            "request_timeout_seconds": config.request_timeout_seconds,
            "command": config.command,
        },
    }


def invoke_command_adapter(config: ResolvedAgentConfig, payload: dict[str, Any]) -> dict[str, Any]:
    if not config.command:
        raise SystemExit("command adapter requires a non-empty command")
    try:
        completed = subprocess.run(
            config.command,
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            timeout=config.request_timeout_seconds,
            check=False,
            cwd=ROOT,
        )
    except OSError as exc:
        raise SystemExit(f"command adapter failed to start: {exc}") from exc
    except subprocess.TimeoutExpired as exc:
        raise SystemExit(
            f"command adapter timed out after {config.request_timeout_seconds} seconds: {exc}"
        ) from exc

    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or f"exit code {completed.returncode}"
        raise SystemExit(f"command adapter failed: {detail}")
    try:
        response = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"command adapter returned invalid JSON: {exc}") from exc
    if not isinstance(response, dict):
        raise SystemExit("command adapter response must be a JSON object")
    if response.get("protocol_version") != ADAPTER_PROTOCOL_VERSION:
        raise SystemExit(
            "command adapter protocol version mismatch: "
            f"expected {ADAPTER_PROTOCOL_VERSION}, got {response.get('protocol_version')!r}"
        )
    return response


def extract_command_candidate(response: dict[str, Any]) -> tuple[str, str]:
    response_text_raw = response.get("response_text_raw")
    response_text = response.get("response_text")
    candidate = response.get("candidate_file_contents")
    if isinstance(candidate, str) and candidate.strip():
        if isinstance(response_text, str):
            return response_text, candidate
        if isinstance(response_text_raw, str):
            return response_text_raw, candidate
        return candidate, candidate

    if isinstance(response_text, str):
        return response_text, extract_candidate_file(response_text)
    if isinstance(response_text_raw, str):
        return response_text_raw, extract_candidate_file(response_text_raw)
    return "", ""


def legacy_result_path(task_ref: str) -> Path:
    return AGENT_RESULTS_DIR / f"{task_ref.replace('/', '__')}.json"


def canonical_result_path(task_ref: str, config: ResolvedAgentConfig) -> Path:
    return AGENT_RESULTS_DIR / config.track / config.run_slug / f"{task_ref.replace('/', '__')}.json"


def canonical_summary_path(config: ResolvedAgentConfig) -> Path:
    return ROOT / "results" / "agent_summaries" / config.track / f"{config.run_slug}.json"


def scoped_summary_path(config: ResolvedAgentConfig, scope: str) -> Path:
    if scope.startswith("suite:"):
        return canonical_summary_path(config)
    slug = slugify(scope.replace(":", "-").replace("/", "-"))
    return ROOT / "results" / "agent_summaries" / config.track / config.run_slug / f"{slug}.json"


def uses_legacy_aliases(config: ResolvedAgentConfig) -> bool:
    return config.track == "reference" and config.config_path == config_label(DEFAULT_AGENT_CONFIG_PATH)


def write_result(task_ref: str, config: ResolvedAgentConfig, payload: dict[str, Any]) -> Path:
    result_path = canonical_result_path(task_ref, config)
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if uses_legacy_aliases(config):
        legacy_path = legacy_result_path(task_ref)
        legacy_path.parent.mkdir(parents=True, exist_ok=True)
        legacy_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return result_path


def build_result(
    task_ref: str,
    config: ResolvedAgentConfig,
    task: dict[str, Any],
    messages: list[dict[str, Any]],
    *,
    dry_run: bool,
    evaluation: dict[str, Any] | None = None,
    elapsed_seconds: float | None = None,
) -> dict[str, Any]:
    payload = {
        "schema_version": 1,
        "task_ref": task_ref,
        "task_id": task["task_id"],
        "case_id": task["case_id"],
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "dry_run": dry_run,
        "status": "dry_run" if dry_run else str((evaluation or {}).get("status", "failed")),
        "theorem_name": task["theorem_name"],
        "proof_family": task["proof_family"],
        "implementation_files": task["implementation_files"],
        "specification_files": task["specification_files"],
        "editable_files": task["editable_files"],
        "agent": {
            "profile": config.profile,
            "agent_id": config.agent_id,
            "mode": config.mode,
            "track": config.track,
            "run_slug": config.run_slug,
            "adapter": config.adapter,
            "config_path": config.config_path,
            "base_url": config.base_url,
            "base_url_env": config.base_url_env,
            "model": config.model,
            "model_env": config.model_env,
            "api_key_env": config.api_key_env,
            "chat_completions_path": config.chat_completions_path,
            "models_path": config.models_path,
            "system_prompt_files": config.system_prompt_files,
            "temperature": config.temperature,
            "max_completion_tokens": config.max_completion_tokens,
            "max_attempts": config.max_attempts,
            "max_tool_calls": config.max_tool_calls,
            "request_timeout_seconds": config.request_timeout_seconds,
            "headers": redact_headers(config.headers),
            "header_envs": config.header_envs,
            "env_contract": config.env_contract,
            "extra_body": config.extra_body,
            "command": config.command,
        },
        "messages": messages,
    }
    if evaluation is not None:
        payload["evaluation"] = evaluation
    if elapsed_seconds is not None:
        payload["elapsed_seconds"] = round(elapsed_seconds, 3)
    return payload


def validate_result_payload(payload: dict[str, Any], label: str) -> None:
    schema = load_json(RUN_SCHEMA_PATH)
    errors = validate(payload, schema, label)
    if errors:
        raise SystemExit("\n".join(errors))


def resolve_task(task_ref: str) -> dict[str, Any]:
    return load_task_record(resolve_task_manifest(task_ref))


def validate_command(config_path: Path) -> int:
    resolve_config(config_path, require_secrets=False)
    print(config_label(config_path))
    return 0


def env_contract(config: dict[str, Any]) -> dict[str, list[str]]:
    required: list[str] = []
    optional: list[str] = []

    for field in ("base_url", "model", "api_key"):
        env_name = normalize_string(config.get(f"{field}_env"))
        if not env_name:
            continue
        if normalize_string(config.get(field)):
            optional.append(env_name)
        else:
            required.append(env_name)

    raw_header_envs = config.get("header_envs", {})
    if isinstance(raw_header_envs, dict):
        for env_name in raw_header_envs.values():
            normalized = normalize_string(env_name)
            if normalized:
                optional.append(normalized)

    return {
        "required": sorted(set(required)),
        "optional": sorted(set(optional)),
    }


def field_source(config: dict[str, Any], field: str) -> str:
    if normalize_string(config.get(field)):
        return "config"
    if normalize_string(config.get(f"{field}_env")):
        return "env"
    return "missing"


def describe_command(config_path: Path) -> int:
    config_data = load_config(config_path)
    config = resolve_config(config_path, require_secrets=False)
    print(
        json.dumps(
            {
                "adapter": config.adapter,
                "agent_id": config.agent_id,
                "mode": config.mode,
                "track": config.track,
                "run_slug": config.run_slug,
                "config_path": config.config_path,
                "base_url": config.base_url or None,
                "base_url_env": config_data.get("base_url_env"),
                "base_url_source": field_source(config_data, "base_url"),
                "model": config.model or None,
                "model_env": config_data.get("model_env"),
                "model_source": field_source(config_data, "model"),
                "api_key_source": field_source(config_data, "api_key"),
                "api_key_env": config_data.get("api_key_env"),
                "chat_completions_path": config.chat_completions_path,
                "models_path": config.models_path,
                "system_prompt_files": config.system_prompt_files,
                "temperature": config.temperature,
                "max_completion_tokens": config.max_completion_tokens,
                "max_attempts": config.max_attempts,
                "max_tool_calls": config.max_tool_calls,
                "headers": redact_headers(config.headers),
                "header_envs": config.header_envs,
                "env_contract": config.env_contract,
                "extra_body": config.extra_body,
                "request_timeout_seconds": config.request_timeout_seconds,
                "command": config.command,
                "api_key_present": bool(config.api_key),
            },
            indent=2,
        )
    )
    return 0


def prompt_command(config_path: Path, task_ref: str) -> int:
    config = resolve_config(config_path, require_secrets=False)
    task = resolve_task(task_ref)
    payload = {
        "task_ref": task_ref,
        "messages": build_messages(config, task),
    }
    print(json.dumps(payload, indent=2))
    return 0


def evaluate_candidate_command(task_ref: str, candidate_path: Path) -> int:
    task = resolve_task(task_ref)
    evaluation = evaluate_candidate_submission(task, candidate_path.read_text(encoding="utf-8"))
    print(json.dumps(evaluation, indent=2))
    return 0 if evaluation["status"] == "passed" else 1


def probe_command(config_path: Path, ensure_model: bool) -> int:
    config = resolve_config(config_path, require_secrets=True)
    if config.adapter == "openai_compatible":
        models_payload = list_models(config)
        model_ids = extract_model_ids(models_payload)
        configured_model_available = config.model in model_ids
        payload = {
            "adapter": config.adapter,
            "mode": config.mode,
            "base_url": config.base_url,
            "models_path": config.models_path,
            "configured_model": config.model,
            "model_count": len(model_ids),
            "models": model_ids,
            "configured_model_available": configured_model_available,
        }
        print(json.dumps(payload, indent=2))
        if ensure_model:
            ensure_configured_model_available(config, model_ids)
        return 0

    probe_task = {
        "task_ref": "__probe__",
        "task_id": "__probe__",
        "case_id": "__probe__",
        "track": config.track,
        "property_class": "",
        "category": "",
        "difficulty": "",
        "theorem_name": "",
        "proof_family": "",
        "implementation_files": [],
        "specification_files": [],
        "editable_files": [],
        "targets": {},
        "evaluation": {},
        "readiness": {},
        "manifest_path": "",
        "case_manifest_path": "",
    }
    payload = invoke_command_adapter(
        config,
        build_command_adapter_request(config, probe_task, [], kind="probe"),
    )
    print(json.dumps(payload, indent=2))
    if ensure_model and payload.get("configured_model_available") is not True:
        raise SystemExit(
            "command adapter probe could not confirm configured model "
            f"{config.model!r}"
        )
    return 0


def execute_strict_agent_task(
    config: ResolvedAgentConfig,
    task: dict[str, Any],
    messages: list[dict[str, Any]],
) -> tuple[dict[str, Any], str, dict[str, Any], list[dict[str, Any]]]:
    attempt_messages = messages
    response: dict[str, Any] = {}
    response_text = ""
    candidate_text = ""
    evaluation: dict[str, Any] = {
        "status": "failed",
        "failure_mode": "agent_not_run",
        "details": "agent invocation did not start",
    }
    attempts: list[dict[str, Any]] = []

    attempt_start = time.perf_counter()
    response = send_chat_completion(config, attempt_messages)
    attempt_latency = time.perf_counter() - attempt_start
    response_text = extract_text(response)
    candidate_text = extract_candidate_file(response_text)
    evaluation = evaluate_candidate_submission(task, candidate_text)
    attempts.append(
        build_attempt_record(
            attempt_index=1,
            mode="strict",
            messages=attempt_messages,
            response=response,
            candidate_text=candidate_text,
            evaluation=evaluation,
            previous_attempt=None,
            latency_seconds=attempt_latency,
        )
    )
    return response, response_text, evaluation, attempts


RESTART_AFTER_CONSECUTIVE_FAILURES = 6


def _compact_interactive_transcript(
    transcript: list[dict[str, Any]],
    base_message_count: int,
    proof_text: str,
    error_details: str,
    attempt_index: int,
    max_attempts: int,
    consecutive_failures: int = 0,
) -> list[dict[str, Any]]:
    """Compact transcript by keeping base messages + first exploration + compact repair.

    We preserve the initial exploration (file reads, searches) but drop intermediate
    failed write-check cycles to prevent context pollution and save tokens.
    The latest failed proof and error are injected as a single user message.

    After RESTART_AFTER_CONSECUTIVE_FAILURES consecutive lean check failures, we drop
    the failed proof from the repair message and instead instruct the model to try a
    completely different proof strategy (a "restart").
    """
    # Find the first write_editable_proof call to split exploration from repair
    cutoff = len(transcript)
    for i, msg in enumerate(transcript):
        if i < base_message_count:
            continue
        if msg.get("role") == "assistant":
            tool_calls = msg.get("tool_calls", [])
            for tc in tool_calls:
                fn = tc.get("function", {})
                if fn.get("name") == "write_editable_proof":
                    cutoff = i
                    break
            if cutoff < len(transcript):
                break

    # Keep base messages + exploration phase (up to first write), then add repair
    kept = transcript[:cutoff]

    if consecutive_failures >= RESTART_AFTER_CONSECUTIVE_FAILURES:
        # Strategy restart: don't show the failed proof, ask for a fresh approach
        repair_msg = (
            f"You have failed {consecutive_failures} consecutive Lean check attempts "
            f"(attempt {attempt_index} of {max_attempts}).\n"
            "Your current approach is not working. Try a fundamentally different proof strategy:\n"
            "- If you were using `simp` with many definitions, try proving with `by_cases` and smaller helper lemmas.\n"
            "- If you were using `by_cases`, try a direct `simp` with all relevant definitions.\n"
            "- If you were using named lemmas, switch to `omega`, `decide`, or `native_decide`.\n"
            "- Consider unfolding the spec first with `unfold` before applying tactics.\n\n"
            f"Last error:\n{error_details[:2000]}\n\n"
            "Submit a completely new proof using write_editable_proof, then call run_lean_check.\n"
        )
    else:
        guidance = build_repair_guidance(error_details)
        repair_msg = (
            f"Your proof attempt (attempt {attempt_index} of {max_attempts}) failed the Lean checker.\n"
            "Fix the proof and resubmit using write_editable_proof, then call run_lean_check.\n\n"
            f"Failed proof:\n```lean\n{proof_text.rstrip()}\n```\n\n"
            f"Lean checker output:\n{error_details}\n"
        )
        if guidance:
            repair_msg += f"\nRepair guidance:\n{guidance}\n"

    kept.append({"role": "user", "content": repair_msg})
    return kept


def execute_interactive_agent_task(
    config: ResolvedAgentConfig,
    task: dict[str, Any],
    messages: list[dict[str, Any]],
) -> tuple[dict[str, Any], str, str, dict[str, Any], list[dict[str, Any]], int]:
    runtime = TaskProofRuntime(task)
    base_messages: list[dict[str, Any]] = list(messages)
    transcript: list[dict[str, Any]] = list(messages)
    attempts: list[dict[str, Any]] = []
    response: dict[str, Any] = {}
    response_text = ""
    tool_calls_used = 0
    last_lean_error: str | None = None
    consecutive_lean_failures = 0
    proof_attempts = 0
    consecutive_search_turns = 0
    consecutive_length_stops = 0
    max_total_turns = config.max_attempts * 2  # hard cap to prevent infinite loops
    token_budget = config.max_completion_tokens

    turn = 0
    while proof_attempts < config.max_attempts and turn < max_total_turns:
        turn += 1
        response = send_chat_completion(
            config, transcript, tools=runtime.tool_specs(),
            max_tokens_override=token_budget if token_budget != config.max_completion_tokens else None,
        )
        response_text = extract_text(response)
        tool_calls = extract_tool_calls(response)

        # Detect finish_reason=length with no usable output (model hit token limit
        # during internal reasoning). Bump token budget and retry without counting
        # this as a proof attempt.
        finish_reason = ""
        choices = response.get("choices", [])
        if choices:
            finish_reason = choices[0].get("finish_reason", "")
        if finish_reason == "length" and not tool_calls and not response_text.strip():
            consecutive_length_stops += 1
            if consecutive_length_stops == 1:
                # First length stop: bump token budget once and retry silently
                token_budget = min(int(token_budget * 1.5), 4500)
                continue
            # Subsequent length stops: inject a nudge to simplify and use tools
            transcript.append({"role": "assistant", "content": ""})
            transcript.append({
                "role": "user",
                "content": (
                    "Your response was cut off. Do not over-think. "
                    "Immediately call write_editable_proof with a simple proof attempt, "
                    "then call run_lean_check. Keep the proof short."
                ),
            })
            if consecutive_length_stops >= 3:
                # Reset budget back to configured value after persistent overruns
                token_budget = config.max_completion_tokens
            continue
        else:
            consecutive_length_stops = 0

        attempts.append(
            {
                "attempt": turn,
                "proof_attempt": proof_attempts + 1,
                "mode": "interactive",
                "messages": list(transcript),
                "response": response,
                "response_text": response_text,
                "tool_calls": tool_calls,
            }
        )
        attempts[-1]["tool_calls"] = tool_calls
        if not tool_calls:
            final_candidate = extract_candidate_file(response_text)
            if final_candidate.strip():
                runtime.write_editable_proof(final_candidate)
                proof_attempts += 1
                evaluation = runtime.evaluate_current()
                attempts[-1]["candidate_file_contents"] = runtime.current_proof_text
                attempts[-1]["evaluation"] = evaluation
                if evaluation["status"] == "passed":
                    return response, response_text, runtime.current_proof_text, evaluation, attempts, tool_calls_used
                # Failed candidate without tool calls: compact and retry
                failure_mode = evaluation.get("failure_mode", "")
                if failure_mode == "lean_check_failed":
                    consecutive_lean_failures += 1
                    details = str(evaluation.get("details", ""))[:MAX_ERROR_FEEDBACK_CHARS]
                    transcript = _compact_interactive_transcript(
                        transcript, len(base_messages), runtime.current_proof_text, details,
                        proof_attempts, config.max_attempts,
                        consecutive_failures=consecutive_lean_failures,
                    )
                elif failure_mode in ("placeholder_detected", "theorem_statement_mismatch"):
                    retry_msg = (
                        f"Your response did not produce a valid proof candidate (proof attempt {proof_attempts} of {config.max_attempts}, "
                        f"failure: {failure_mode}).\n"
                        "Use the write_editable_proof tool to submit the complete editable Lean proof file, "
                        "then use run_lean_check to verify it.\n"
                        "Do not explain or analyze. Use the tools directly.\n"
                    )
                    transcript.append({"role": "assistant", "content": response_text})
                    transcript.append({"role": "user", "content": retry_msg})
                else:
                    return response, response_text, runtime.current_proof_text, evaluation, attempts, tool_calls_used
            else:
                # Empty response or no valid candidate: nudge model to use tools
                nudge_msg = (
                    "You must use the write_editable_proof tool to submit your proof, "
                    "then call run_lean_check to verify it. Do not respond with text only.\n"
                )
                transcript.append({"role": "assistant", "content": response_text or ""})
                transcript.append({"role": "user", "content": nudge_msg})
            continue

        transcript.append(
            {
                "role": "assistant",
                "content": response_text,
                "tool_calls": tool_calls,
            }
        )
        saw_lean_failure = False
        turn_had_proof_action = False
        for tool_call in tool_calls:
            if tool_calls_used >= config.max_tool_calls:
                evaluation = runtime.evaluate_current()
                if evaluation.get("failure_mode") == "empty_response":
                    evaluation = {
                        "status": "failed",
                        "failure_mode": "tool_budget_exhausted",
                        "details": f"interactive tool-call budget exhausted after {tool_calls_used} tool calls",
                    }
                attempts[-1]["budget_exhausted"] = True
                attempts[-1]["candidate_file_contents"] = runtime.current_proof_text
                attempts[-1]["evaluation"] = evaluation
                return response, response_text, runtime.current_proof_text, evaluation, attempts, tool_calls_used
            function_call = tool_call.get("function", {})
            tool_name = str(function_call.get("name", ""))
            arguments = parse_tool_arguments(function_call.get("arguments"))
            result = runtime.execute_tool(tool_name, arguments)
            tool_calls_used += 1
            if tool_name in ("write_editable_proof", "run_lean_check"):
                turn_had_proof_action = True
            transcript.append(
                {
                    "role": "tool",
                    "tool_call_id": str(tool_call.get("id", "")),
                    "content": tool_result_json(result),
                }
            )
            attempts[-1].setdefault("tool_results", []).append(
                {
                    "tool_call_id": str(tool_call.get("id", "")),
                    "name": tool_name,
                    "arguments": arguments,
                    "result": result,
                }
            )
            if tool_name == "run_lean_check" and result.get("failure_mode") == "lean_check_failed":
                last_lean_error = str(result.get("details", ""))[:MAX_ERROR_FEEDBACK_CHARS]
                saw_lean_failure = True
                consecutive_lean_failures += 1
            elif tool_name == "run_lean_check" and result.get("status") == "passed":
                evaluation = result
                attempts[-1]["candidate_file_contents"] = runtime.current_proof_text
                attempts[-1]["evaluation"] = evaluation
                return response, response_text, runtime.current_proof_text, evaluation, attempts, tool_calls_used

        if turn_had_proof_action:
            proof_attempts += 1
            consecutive_search_turns = 0
            if not saw_lean_failure:
                consecutive_lean_failures = 0
        else:
            consecutive_search_turns += 1
            if consecutive_search_turns >= 2:
                transcript.append(
                    {
                        "role": "user",
                        "content": (
                            "Stop searching and write a proof now. The search_public_defs tool only searches "
                            "this task's implementation and specification files, not the Lean standard library. "
                            "Use write_editable_proof to submit your best proof attempt, then run_lean_check to verify."
                        ),
                    }
                )
                consecutive_search_turns = 0

        # After processing all tool calls, compact transcript if we saw a lean failure
        if saw_lean_failure and last_lean_error:
            transcript = _compact_interactive_transcript(
                transcript, len(base_messages), runtime.current_proof_text, last_lean_error,
                proof_attempts, config.max_attempts,
                consecutive_failures=consecutive_lean_failures,
            )

    evaluation = runtime.evaluate_current()
    if evaluation.get("failure_mode") == "empty_response":
        evaluation = {
            "status": "failed",
            "failure_mode": "attempt_budget_exhausted",
            "details": f"interactive attempt budget exhausted after {proof_attempts} proof attempts ({turn} total turns)",
        }
    attempts.append(
        {
            "attempt": turn,
            "proof_attempt": proof_attempts,
            "mode": "interactive",
            "budget_exhausted": True,
            "candidate_file_contents": runtime.current_proof_text,
            "evaluation": evaluation,
        }
    )
    attempts[-1]["budget_exhausted"] = True
    return response, response_text, runtime.current_proof_text, evaluation, attempts, tool_calls_used


def execute_agent_task(
    config_path: Path,
    task_ref: str,
    dry_run: bool,
    *,
    profile: str | None = None,
    resolved_config: ResolvedAgentConfig | None = None,
) -> tuple[int, Path]:
    config = resolved_config or resolve_config(config_path, require_secrets=not dry_run, profile=profile)
    task = resolve_task(task_ref)
    messages = build_messages(config, task)
    if dry_run:
        result = build_result(task_ref, config, task, messages, dry_run=dry_run, elapsed_seconds=0.0)
        validate_result_payload(result, task_ref)
        result_path = write_result(task_ref, config, result)
        return 0, result_path

    start = time.perf_counter()
    if config.mode == "interactive":
        response, response_text, candidate_text, evaluation, attempts, tool_calls_used = execute_interactive_agent_task(
            config,
            task,
            messages,
        )
    elif config.mode == "custom":
        response = invoke_command_adapter(
            config,
            build_command_adapter_request(config, task, messages, kind="run"),
        )
        response_text, candidate_text = extract_command_candidate(response)
        evaluation = evaluate_candidate_submission(task, candidate_text)
        attempts = []
        tool_calls_used = 0
    else:
        response, response_text, evaluation, attempts = execute_strict_agent_task(config, task, messages)
        candidate_text = str(attempts[-1].get("candidate_file_contents", "")) if attempts else ""
        tool_calls_used = 0
    elapsed_seconds = time.perf_counter() - start
    result = build_result(
        task_ref,
        config,
        task,
        messages,
        dry_run=dry_run,
        evaluation=evaluation,
        elapsed_seconds=elapsed_seconds,
    )
    result["response"] = response
    result["response_text"] = response_text
    if config.mode == "custom":
        result["response_text_raw"] = str(response.get("response_text_raw", response_text))
        result["provider_reasoning_text"] = str(response.get("provider_reasoning_text", ""))
    else:
        response_content = extract_response_content(response)
        result["response_text_raw"] = response_content["response_text_raw"]
        result["provider_reasoning_text"] = response_content["provider_reasoning_text"]
    result["candidate_file_contents"] = candidate_text
    result["attempts"] = attempts
    result["tool_calls_used"] = tool_calls_used
    result["analysis"] = build_run_analysis(attempts=attempts, evaluation=evaluation, tool_calls_used=tool_calls_used)
    validate_result_payload(result, task_ref)
    result_path = write_result(task_ref, config, result)
    return (0 if evaluation["status"] == "passed" else 1), result_path


def run_command(config_path: Path, task_ref: str, dry_run: bool, *, profile: str | None = None) -> int:
    exit_code, result_path = execute_agent_task(config_path, task_ref, dry_run, profile=profile)
    print(result_path.relative_to(ROOT))
    return exit_code


def profiles_command() -> int:
    profiles: list[dict[str, Any]] = []
    for name in discover_profiles():
        path = profile_path(name)
        config = load_config(path)
        profiles.append(
            {
                "name": name,
                "agent_id": config["agent_id"],
                "mode": config.get("mode"),
                "track": config.get("track"),
                "run_slug": config.get("run_slug"),
                "adapter": config["adapter"],
                "config_path": config_label(path),
                "env_contract": env_contract(config),
            }
        )
    payload = {
        "profiles_dir": config_label(AGENT_PROFILES_DIR),
        "default_profile": DEFAULT_PROFILE,
        "profiles": profiles,
    }
    print(json.dumps(payload, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Default benchmark agent adapter")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate-config", help="Validate an agent config file")
    validate_parser.add_argument("config")

    describe_parser = subparsers.add_parser("describe", help="Resolve and print a non-secret config summary")
    describe_parser.add_argument("--config")
    describe_parser.add_argument("--profile")

    prompt_parser = subparsers.add_parser("prompt", help="Render the default-agent prompt package for one task")
    prompt_parser.add_argument("task_ref")
    prompt_parser.add_argument("--config")
    prompt_parser.add_argument("--profile")

    evaluate_parser = subparsers.add_parser(
        "evaluate-candidate",
        help="Evaluate a candidate editable Lean file for one task",
    )
    evaluate_parser.add_argument("task_ref")
    evaluate_parser.add_argument("candidate_path")

    probe_parser = subparsers.add_parser("probe", help="Probe the configured OpenAI-compatible backend")
    probe_parser.add_argument("--config")
    probe_parser.add_argument("--profile")
    probe_parser.add_argument("--ensure-model", action="store_true")

    run_parser = subparsers.add_parser("run", help="Invoke the configured default agent for one task")
    run_parser.add_argument("task_ref")
    run_parser.add_argument("--config")
    run_parser.add_argument("--profile")
    run_parser.add_argument("--dry-run", action="store_true")

    subparsers.add_parser("profiles", help="List bundled default-agent profiles")

    args = parser.parse_args()

    if args.command == "validate-config":
        return validate_command(explicit_config_path(args.config))
    if args.command == "describe":
        return describe_command(resolve_config_path(args.config, args.profile))
    if args.command == "prompt":
        return prompt_command(resolve_config_path(args.config, args.profile), args.task_ref)
    if args.command == "evaluate-candidate":
        return evaluate_candidate_command(args.task_ref, Path(args.candidate_path))
    if args.command == "probe":
        return probe_command(resolve_config_path(args.config, args.profile), args.ensure_model)
    if args.command == "run":
        return run_command(
            resolve_config_path(args.config, args.profile),
            args.task_ref,
            args.dry_run,
            profile=args.profile,
        )
    if args.command == "profiles":
        return profiles_command()

    print(f"unsupported command: {args.command}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
