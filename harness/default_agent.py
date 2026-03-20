#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error, request

from benchmark_config import load_benchmark_agent_defaults
from task_runner import ROOT, load_task_record, resolve_task_manifest, run_command as lean_run_command

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
    temperature: float
    max_completion_tokens: int
    max_attempts: int
    headers: dict[str, str]
    header_envs: dict[str, str]
    env_contract: dict[str, list[str]]
    extra_body: dict[str, Any]
    request_timeout_seconds: int


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
    for field in ("agent_id", "run_slug"):
        if not normalize_string(config.get(field)):
            errors.append(f"{label}: {field!r} must be a non-empty string")

    for field in ("base_url", "model", "api_key"):
        direct_value = normalize_string(config.get(field))
        env_name = normalize_string(config.get(f"{field}_env"))
        if direct_value or env_name:
            continue
        errors.append(f"{label}: set either {field!r} or {field + '_env'!r}")

    if config.get("adapter") == "openai_compatible":
        for field in ("chat_completions_path", "models_path"):
            value = normalize_string(config.get(field))
            if not value:
                errors.append(f"{label}: {field!r} must be a non-empty string")
            elif not value.startswith("/"):
                errors.append(f"{label}: {field!r} must start with '/' for openai_compatible adapters")

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


def resolve_config(path: Path, *, require_secrets: bool, profile: str | None = None) -> ResolvedAgentConfig:
    config = load_config(path)
    agent_id = str(config["agent_id"])
    prompt_files = [str(item) for item in config["system_prompt_files"]]
    missing_files = [item for item in prompt_files if not (ROOT / item).is_file()]
    if missing_files:
        raise SystemExit(f"missing system prompt files: {', '.join(missing_files)}")

    return ResolvedAgentConfig(
        profile=profile,
        agent_id=agent_id,
        track=resolve_track(config, profile=profile),
        run_slug=resolve_run_slug(config, agent_id=agent_id, profile=profile),
        adapter=str(config["adapter"]),
        config_path=config_label(path),
        base_url=(resolve_field(config, "base_url", required=require_secrets) or "").rstrip("/"),
        base_url_env=normalize_string(config.get("base_url_env")),
        model=resolve_field(config, "model", required=require_secrets) or "",
        model_env=normalize_string(config.get("model_env")),
        api_key=resolve_field(config, "api_key", required=require_secrets) or "",
        api_key_env=normalize_string(config.get("api_key_env")),
        chat_completions_path=str(config["chat_completions_path"]),
        models_path=str(config.get("models_path", "/models")),
        system_prompt_files=prompt_files,
        temperature=float(config["temperature"]),
        max_completion_tokens=int(config["max_completion_tokens"]),
        max_attempts=int(config.get("max_attempts", 5)),
        headers=resolve_headers(config),
        header_envs={str(key): str(value) for key, value in dict(config.get("header_envs", {})).items()},
        env_contract=env_contract(config),
        extra_body=dict(config.get("extra_body", {})),
        request_timeout_seconds=int(config.get("request_timeout_seconds", 120)),
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
        "Useful simplification symbols are often: `getStorage`, `setStorage`, `setMapping`, `setMappingUint`, `Verity.require`, `Verity.bind`, `Bind.bind`, `Verity.pure`, `Pure.pure`, `Contract.run`, and `ContractResult.snd`.",
        "Include the contract's storage labels in the simp set when relevant, for example fields such as `RammPriceBand.capital` or `DepositContractMinimal.depositCount`.",
        "If helpful, you may add imports required for proof automation, for example `import Verity.Proofs.Stdlib.Automation`.",
        "When a branch guard is not directly in the right form for `simp`, derive a helper fact first, then simplify.",
        "If `simp` gets stuck on a conditional execution path, prove branch-specific private helper theorems with explicit hypotheses instead of trying to split the final `match` state directly.",
    ]
    family_specific: list[str] = []
    if family == "state_preservation_local_effects":
        family_specific = [
            "For local-effect theorems, a good pattern is: unfold the spec, split on relevant branch conditions, prove concrete slot-write equalities, then finish with `simpa`.",
            "A private helper theorem that proves several slot writes at once can make the final theorem much shorter.",
            "When the contract branches on a threshold, use `by_cases` on the branch condition in the public theorem and a negated helper fact such as `Nat.not_le_of_lt hSmall` for the non-branch case.",
        ]
    elif family == "protocol_transition_correctness":
        family_specific = [
            "For transition theorems, use `by_cases` on threshold guards and threshold equalities before simplifying the execution trace.",
            "For hypotheses of the form `hSmall : x < c`, the corresponding negated branch fact is often `have hNotBranch : ¬ c ≤ x := Nat.not_le_of_lt hSmall`.",
        ]
    elif family == "authorization_enablement":
        family_specific = [
            "For authorization theorems, unfold the spec and simplify the guarded execution path using the provided permission hypotheses.",
        ]
    elif family == "refinement_equivalence":
        family_specific = [
            "For refinement/equivalence theorems, first normalize both sides into the same post-state shape, then prove the observable fields agree.",
        ]
    elif family == "functional_correctness":
        family_specific = [
            "For functional-correctness theorems, unfold the spec to the mathematical target form before simplifying the execution result.",
        ]
    lines = ["Public proof hints:"] + [f"- {item}" for item in [*shared, *family_specific]]
    return "\n".join(lines)


def build_user_prompt(task: dict[str, Any]) -> str:
    editable_file = task["editable_files"][0]
    return (
        "You are running the default benchmark agent for verity-benchmark.\n"
        "Treat this as a strict proof-generation benchmark.\n"
        "Do not invent specs, modify implementations, or rely on hidden reference proofs.\n\n"
        "The harness may give you several bounded repair rounds for the same task.\n"
        "On every round, return the complete editable Lean proof file, not a patch or explanation.\n"
        "Do not claim that you will inspect more files or run commands.\n"
        "Reason only from the task payload and the file contents included below.\n"
        "Return the complete contents of the single editable Lean proof file.\n"
        "Return Lean code only, with no markdown fences or extra explanation.\n\n"
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
        {"role": "user", "content": build_user_prompt(task)},
    ]


def build_repair_messages(
    base_messages: list[dict[str, str]],
    candidate_text: str,
    evaluation: dict[str, Any],
    *,
    attempt_index: int,
    max_attempts: int,
) -> list[dict[str, str]]:
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


def build_repair_guidance(details: str) -> str:
    hints: list[str] = []
    if "tactic 'split' failed" in details:
        hints.append(
            "- Do not `split` the final post-state blindly. Prove branch-specific helper theorems first, then use `by_cases` plus `simpa`."
        )
    if "no goals to be solved" in details:
        hints.append(
            "- A previous `simp` likely closed the goal already. Remove trailing tactics such as `decide`, `exact`, or extra `simp` calls after the goal is solved."
        )
    if "expected type must not contain free variables" in details:
        hints.append(
            "- Do not use `native_decide` or `decide` on goals that still contain parameters. First reduce to concrete slot-number equalities with `have` facts or extra `simp`; only then use `native_decide` if the remaining goal is fully decidable."
        )
    if "Unknown identifier" in details:
        hints.append(
            "- Fix typos or missing imports directly; prefer standard names such as `Nat.lt_of_not_ge` and `Nat.not_le_of_lt`."
        )
    if "unsolved goals" in details and "if " in details:
        hints.append(
            "- If `simp` leaves concrete slot comparisons or small `if` expressions, finish those residual finite equalities with `native_decide` or `decide`."
        )
    if "unsolved goals" in details and "32000000000" in details:
        hints.append(
            "- The generated code often uses the comparator form `32000000000 ≤ depositAmount`. Derive the exact branch fact needed by `simp`, for example `have hNotFull : ¬ 32000000000 ≤ depositAmount := Nat.not_le_of_lt hSmall`."
        )
    return "\n".join(hints)


def reasoning_excerpt(response: dict[str, Any]) -> str:
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    message = choices[0].get("message", {})
    reasoning_content = message.get("reasoning_content")
    if isinstance(reasoning_content, str):
        return reasoning_content.strip()[:MAX_REASONING_SNIPPET_CHARS]
    return ""


def build_finalization_messages(
    base_messages: list[dict[str, str]],
    response: dict[str, Any],
    *,
    attempt_index: int,
    max_attempts: int,
) -> list[dict[str, str]]:
    reasoning = reasoning_excerpt(response)
    prompt = (
        f"Your previous reply did not include a final Lean file (attempt {attempt_index} of {max_attempts}).\n"
        "Stop reasoning and return the complete contents of the editable Lean proof file now.\n"
        "Return Lean code only, with no markdown fences or extra explanation.\n"
        "Prefer a short proof built from private helper theorems plus `simp`/`simpa`.\n"
    )
    if reasoning:
        prompt += (
            "\nPrevious internal draft excerpt:\n"
            f"{reasoning}\n"
        )
    return [
        *base_messages,
        {"role": "user", "content": prompt},
    ]


def send_chat_completion(config: ResolvedAgentConfig, messages: list[dict[str, str]]) -> dict[str, Any]:
    url = f"{config.base_url}{config.chat_completions_path}"
    payload = {
        "model": config.model,
        "messages": messages,
        "temperature": config.temperature,
        "max_tokens": config.max_completion_tokens,
    }
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
    return json.loads(body)


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
    return json.loads(body)


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
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    message = choices[0].get("message", {})
    content = message.get("content")
    if isinstance(content, str):
        text = content.strip()
        if text:
            return re.sub(r"(?s)<think>.*?</think>\s*", "", content).strip()
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
        joined = "\n".join(parts).strip()
        if joined:
            return re.sub(r"(?s)<think>.*?</think>\s*", "", joined).strip()
    reasoning_content = message.get("reasoning_content")
    if isinstance(reasoning_content, str):
        return reasoning_content
    return ""


def extract_candidate_file(response_text: str) -> str:
    text = response_text.strip()
    fenced = re.findall(r"```(?:lean)?\s*\n(.*?)```", text, flags=re.DOTALL)
    if len(fenced) == 1:
        return fenced[0].strip() + "\n"
    return text + ("\n" if text and not text.endswith("\n") else "")


def evaluate_candidate_submission(task: dict[str, Any], candidate_text: str) -> dict[str, Any]:
    editable_files = task["editable_files"]
    if len(editable_files) != 1:
        return {
            "status": "failed",
            "failure_mode": "editable_file_contract_invalid",
            "details": "tasks must declare exactly one editable Lean file",
        }

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

    editable_rel_path = editable_files[0]
    theorem_name = str(task["theorem_name"])

    with tempfile.TemporaryDirectory(prefix="verity-benchmark-agent-") as tmp_dir:
        workspace = Path(tmp_dir) / "workspace"
        workspace.mkdir(parents=True, exist_ok=True)
        for rel_path in ("lakefile.lean", "lake-manifest.json", "lean-toolchain", ".lake", "Benchmark.lean"):
            source = ROOT / rel_path
            target = workspace / rel_path
            if source.exists():
                os.symlink(source, target, target_is_directory=source.is_dir())
        benchmark_dir = workspace / "Benchmark"
        benchmark_dir.mkdir(parents=True, exist_ok=True)
        for rel_path in ("Benchmark/Cases", "Benchmark/Cases.lean"):
            source = ROOT / rel_path
            target = workspace / rel_path
            target.parent.mkdir(parents=True, exist_ok=True)
            if source.exists():
                os.symlink(source, target, target_is_directory=source.is_dir())
        editable_path = workspace / editable_rel_path
        editable_path.parent.mkdir(parents=True, exist_ok=True)
        editable_path.write_text(candidate_text, encoding="utf-8")

        check_path = workspace / "CandidateCheck.lean"
        check_path.write_text(
            candidate_text.rstrip() + f"\n\n#check {theorem_name}\n",
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


def legacy_result_path(task_ref: str) -> Path:
    return AGENT_RESULTS_DIR / f"{task_ref.replace('/', '__')}.json"


def canonical_result_path(task_ref: str, config: ResolvedAgentConfig) -> Path:
    return AGENT_RESULTS_DIR / config.track / config.run_slug / f"{task_ref.replace('/', '__')}.json"


def canonical_summary_path(config: ResolvedAgentConfig) -> Path:
    return ROOT / "results" / "agent_summaries" / config.track / f"{config.run_slug}.json"


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
    messages: list[dict[str, str]],
    *,
    dry_run: bool,
    evaluation: dict[str, Any] | None = None,
    elapsed_seconds: float | None = None,
) -> dict[str, Any]:
    task = resolve_task(task_ref)
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
                "request_timeout_seconds": config.request_timeout_seconds,
            "headers": config.headers,
            "header_envs": config.header_envs,
            "env_contract": config.env_contract,
            "extra_body": config.extra_body,
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
                "headers": config.headers,
                "header_envs": config.header_envs,
                "env_contract": config.env_contract,
                "extra_body": config.extra_body,
                "request_timeout_seconds": config.request_timeout_seconds,
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
    models_payload = list_models(config)
    model_ids = extract_model_ids(models_payload)
    configured_model_available = config.model in model_ids
    payload = {
        "adapter": config.adapter,
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
        result = build_result(task_ref, config, messages, dry_run=dry_run, elapsed_seconds=0.0)
        validate_result_payload(result, task_ref)
        result_path = write_result(task_ref, config, result)
        return 0, result_path

    start = time.perf_counter()
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

    for attempt_index in range(1, config.max_attempts + 1):
        response = send_chat_completion(config, attempt_messages)
        response_text = extract_text(response)
        candidate_text = extract_candidate_file(response_text)
        evaluation = evaluate_candidate_submission(task, candidate_text)
        attempts.append(
            {
                "attempt": attempt_index,
                "messages": attempt_messages,
                "response": response,
                "response_text": response_text,
                "candidate_file_contents": candidate_text,
                "evaluation": evaluation,
            }
        )
        if evaluation["status"] == "passed":
            break
        if evaluation.get("failure_mode") == "empty_response":
            attempt_messages = build_finalization_messages(
                messages,
                response,
                attempt_index=attempt_index,
                max_attempts=config.max_attempts,
            )
            continue
        if evaluation.get("failure_mode") != "lean_check_failed" or not candidate_text.strip():
            break
        attempt_messages = build_repair_messages(
            messages,
            candidate_text,
            evaluation,
            attempt_index=attempt_index,
            max_attempts=config.max_attempts,
        )

    elapsed_seconds = time.perf_counter() - start
    result = build_result(
        task_ref,
        config,
        messages,
        dry_run=dry_run,
        evaluation=evaluation,
        elapsed_seconds=elapsed_seconds,
    )
    result["response"] = response
    result["response_text"] = response_text
    result["candidate_file_contents"] = candidate_text
    result["attempts"] = attempts
    validate_result_payload(result, task_ref)
    result_path = write_result(task_ref, config, result)
    return (0 if evaluation["status"] == "passed" else 1), result_path


def run_command(config_path: Path, task_ref: str, dry_run: bool, *, profile: str | None = None) -> int:
    _, result_path = execute_agent_task(config_path, task_ref, dry_run, profile=profile)
    print(result_path.relative_to(ROOT))
    return 0


def profiles_command() -> int:
    profiles: list[dict[str, Any]] = []
    for name in discover_profiles():
        path = profile_path(name)
        config = load_config(path)
        profiles.append(
            {
                "name": name,
                "agent_id": config["agent_id"],
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
