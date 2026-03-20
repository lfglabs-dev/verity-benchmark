#!/usr/bin/env bash
set -euo pipefail

if [[ "${VERITY_BENCHMARK_DOTENVX_LOADED:-}" != "1" ]]; then
  exec "$(dirname "$0")/exec_with_dotenvx.sh" "$0" "$@"
fi

cd "$(dirname "$0")/.."
DEFAULT_AGENT_PROFILE="$(python3 - <<'PY'
from pathlib import Path
import sys

sys.path.insert(0, str(Path("harness").resolve()))
from toml_compat import load_toml_file

print(load_toml_file(Path("benchmark.toml"))["default_agent_default_profile"])
PY
)"
CUSTOM_AGENT_PROFILE="$(python3 - <<'PY'
from pathlib import Path
import sys

sys.path.insert(0, str(Path("harness").resolve()))
from toml_compat import load_toml_file

print(load_toml_file(Path("benchmark.toml"))["custom_agent_default_profile"])
PY
)"
RUN_LIVE_AGENT_CHECKS="${VERITY_BENCHMARK_RUN_LIVE_AGENT_CHECKS:-0}"

python3 harness/default_agent.py profiles
python3 harness/default_agent.py validate-config "harness/agents/${DEFAULT_AGENT_PROFILE}.json"
python3 harness/default_agent.py validate-config "harness/agents/${CUSTOM_AGENT_PROFILE}.json"
python3 harness/default_agent.py validate-config harness/agents/openai-proxy-fast.json
python3 harness/default_agent.py validate-config harness/default-agent.example.json
python3 harness/default_agent.py validate-config "$(pwd)/harness/default-agent.example.json"
python3 - <<'PY'
from pathlib import Path
import sys

sys.path.insert(0, str(Path("harness").resolve()))

from default_agent import build_user_prompt, resolve_task

prompt = build_user_prompt(resolve_task("ethereum/deposit_contract_minimal/deposit_count"), interactive=False)
required_snippets = [
    "The harness may give you several bounded repair rounds for the same task.",
    "Implementation file contents:",
    "Specification file contents:",
    "Editable proof template contents:",
    "[Benchmark/Generated/Ethereum/DepositContractMinimal/Tasks/DepositCount.lean]",
    "deposit_increments_deposit_count",
]
missing = [snippet for snippet in required_snippets if snippet not in prompt]
if missing:
    raise SystemExit(f"default-agent prompt is missing expected context: {missing}")
PY
python3 harness/agent_runner.py run ethereum/deposit_contract_minimal/deposit_count --profile "$DEFAULT_AGENT_PROFILE" --dry-run
python3 harness/agent_runner.py run-case ethereum/deposit_contract_minimal --profile "$DEFAULT_AGENT_PROFILE" --dry-run
python3 harness/agent_runner.py run ethereum/deposit_contract_minimal/deposit_count --profile "$CUSTOM_AGENT_PROFILE" --dry-run
python3 harness/agent_runner.py run ethereum/deposit_contract_minimal/deposit_count --profile openai-proxy-fast --dry-run
python3 harness/agent_runner.py run ethereum/deposit_contract_minimal/deposit_count --config harness/default-agent.example.json --dry-run
python3 - <<'PY'
from pathlib import Path
import json

payload = json.loads(
    Path("results/agent_runs/reference/default/ethereum__deposit_contract_minimal__deposit_count.json").read_text(
        encoding="utf-8"
    )
)
elapsed = payload.get("elapsed_seconds")
if not isinstance(elapsed, (int, float)) or elapsed < 0:
    raise SystemExit(f"expected non-negative elapsed_seconds in run artifact, got {elapsed!r}")
PY
python3 - <<'PY'
from pathlib import Path
import sys

sys.path.insert(0, str(Path("harness").resolve()))

from default_agent import ResolvedAgentConfig, ensure_configured_model_available

config = ResolvedAgentConfig(
    profile="test",
    agent_id="agent",
    mode="strict",
    track="custom",
    run_slug="test",
    adapter="openai_compatible",
    config_path="harness/agents/openai-compatible.json",
    base_url="https://agent-backend.thomas.md/v1",
    base_url_env="VERITY_BENCHMARK_AGENT_BASE_URL",
    model="builtin/fast",
    model_env="VERITY_BENCHMARK_AGENT_MODEL",
    api_key="sk-test",
    api_key_env="VERITY_BENCHMARK_AGENT_API_KEY",
    chat_completions_path="/chat/completions",
    models_path="/models",
    system_prompt_files=[],
    temperature=0.0,
    max_completion_tokens=1,
    max_attempts=1,
    max_tool_calls=1,
    lean_checks_amount=0,
    headers={},
    header_envs={},
    env_contract={"required": [], "optional": []},
    extra_body={},
    request_timeout_seconds=1,
    command=[],
)

try:
    ensure_configured_model_available(config, [])
except SystemExit as exc:
    if "no parseable model ids" not in str(exc):
        raise
else:
    raise SystemExit("expected ensure_configured_model_available to reject empty model discovery")

ensure_configured_model_available(config, ["builtin/fast"])
PY
python3 - <<'PY'
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path("harness").resolve()))

from default_agent import extract_text, resolve_task
from interactive_runtime import TaskProofRuntime

task = resolve_task("ethereum/deposit_contract_minimal/deposit_count")
runtime = TaskProofRuntime(task)

with tempfile.TemporaryDirectory() as tmp_dir:
    workspace = Path(tmp_dir) / "workspace"
    runtime._materialize_workspace(workspace)
    editable_path = workspace / task["editable_files"][0]
    if editable_path.is_symlink():
        raise SystemExit("editable proof file should be copied into workspace, not symlinked")

original = runtime.current_proof_text
variant = original.replace(":= by", ":= (by", 1).rstrip() + "\n)\n"
if runtime._extract_theorem_signature(original) != runtime._extract_theorem_signature(variant):
    raise SystemExit("theorem signature extraction should accept equivalent proof-term syntax")

reasoning_only = {
    "choices": [
        {
            "message": {
                "content": "",
                "reasoning_content": "internal chain-of-thought",
            }
        }
    ]
}
if extract_text(reasoning_only) != "":
    raise SystemExit("reasoning-only responses should not be treated as candidate proof text")
PY
python3 - <<'PY'
from pathlib import Path
import sys

sys.path.insert(0, str(Path("harness").resolve()))

import default_agent
from default_agent import ResolvedAgentConfig, build_messages, execute_interactive_agent_task, resolve_task

task = resolve_task("ethereum/deposit_contract_minimal/deposit_count")
config = ResolvedAgentConfig(
    profile="interactive-test",
    agent_id="agent",
    mode="interactive",
    track="custom",
    run_slug="interactive-test",
    adapter="openai_compatible",
    config_path="harness/agents/interactive.json",
    base_url="https://example.invalid",
    base_url_env=None,
    model="builtin/smart",
    model_env="VERITY_BENCHMARK_AGENT_MODEL",
    api_key="sk-test",
    api_key_env="VERITY_BENCHMARK_AGENT_API_KEY",
    chat_completions_path="/chat/completions",
    models_path="/models",
    system_prompt_files=[],
    temperature=0.0,
    max_completion_tokens=1,
    max_attempts=2,
    max_tool_calls=1,
    lean_checks_amount=1,
    headers={},
    header_envs={},
    env_contract={"required": [], "optional": []},
    extra_body={},
    request_timeout_seconds=1,
    command=[],
)

responses = iter([
    {"choices": [{"message": {"content": ""}}]},
    {"choices": [{"message": {"content": ""}}]},
])
original_send = default_agent.send_chat_completion
original_evaluate = default_agent.TaskProofRuntime.evaluate_current
default_agent.send_chat_completion = lambda *_args, **_kwargs: next(responses)
default_agent.TaskProofRuntime.evaluate_current = lambda self, **_kwargs: {
    "status": "failed",
    "failure_mode": "empty_response",
    "details": "agent response was empty",
}
try:
    _, _, _, evaluation, attempts, _ = execute_interactive_agent_task(config, task, build_messages(config, task))
finally:
    default_agent.send_chat_completion = original_send
    default_agent.TaskProofRuntime.evaluate_current = original_evaluate

if len(attempts) < 2:
    raise SystemExit("interactive mode should retry after an empty final response")
if evaluation.get("failure_mode") != "missing_required_tool_use":
    raise SystemExit(f"expected missing_required_tool_use, got {evaluation!r}")
PY
python3 - <<'PY'
from pathlib import Path
import sys

sys.path.insert(0, str(Path("harness").resolve()))

import default_agent
from default_agent import ResolvedAgentConfig, build_messages, execute_interactive_agent_task, resolve_task

task = resolve_task("ethereum/deposit_contract_minimal/deposit_count")
config = ResolvedAgentConfig(
    profile="interactive-test",
    agent_id="agent",
    mode="interactive",
    track="custom",
    run_slug="interactive-test",
    adapter="openai_compatible",
    config_path="harness/agents/interactive.json",
    base_url="https://example.invalid",
    base_url_env=None,
    model="builtin/smart",
    model_env="VERITY_BENCHMARK_AGENT_MODEL",
    api_key="sk-test",
    api_key_env="VERITY_BENCHMARK_AGENT_API_KEY",
    chat_completions_path="/chat/completions",
    models_path="/models",
    system_prompt_files=[],
    temperature=0.0,
    max_completion_tokens=1,
    max_attempts=3,
    max_tool_calls=2,
    lean_checks_amount=0,
    headers={},
    header_envs={},
    env_contract={"required": [], "optional": []},
    extra_body={},
    request_timeout_seconds=1,
    command=[],
)

bad_proof = Path(task["editable_files"][0]).read_text(encoding="utf-8").replace("by\n  sorry", "by\n  exact 0")
responses = iter([
    {
        "choices": [
            {
                "message": {
                    "content": "",
                    "tool_calls": [
                        {
                            "id": "call-1",
                            "type": "function",
                            "function": {
                                "name": "write_editable_proof",
                                "arguments": "{\"content\": " + default_agent.json.dumps(bad_proof) + "}",
                            },
                        }
                    ],
                }
            }
        ]
    },
    {"choices": [{"message": {"content": ""}}]},
    {"choices": [{"message": {"content": ""}}]},
])
original_send = default_agent.send_chat_completion
original_evaluate = default_agent.TaskProofRuntime.evaluate_current
default_agent.send_chat_completion = lambda *_args, **_kwargs: next(responses)
default_agent.TaskProofRuntime.evaluate_current = lambda self, **_kwargs: {
    "status": "failed",
    "failure_mode": "lean_check_failed",
    "details": "simulated checker failure",
}
try:
    _, _, _, _, attempts, _ = execute_interactive_agent_task(config, task, build_messages(config, task))
finally:
    default_agent.send_chat_completion = original_send
    default_agent.TaskProofRuntime.evaluate_current = original_evaluate

repair_prompt = attempts[2]["messages"][-1]["content"]
if "Lean checker output:" not in repair_prompt:
    raise SystemExit("expected tool-written invalid proof to feed checker output into the next repair prompt")
PY
python3 - <<'PY'
from pathlib import Path
import sys

sys.path.insert(0, str(Path("harness").resolve()))

import default_agent
from default_agent import ResolvedAgentConfig, build_messages, execute_interactive_agent_task, resolve_task

task = resolve_task("ethereum/deposit_contract_minimal/deposit_count")
config = ResolvedAgentConfig(
    profile="interactive-test",
    agent_id="agent",
    mode="interactive",
    track="custom",
    run_slug="interactive-test",
    adapter="openai_compatible",
    config_path="harness/agents/interactive.json",
    base_url="https://example.invalid",
    base_url_env=None,
    model="builtin/smart",
    model_env="VERITY_BENCHMARK_AGENT_MODEL",
    api_key="sk-test",
    api_key_env="VERITY_BENCHMARK_AGENT_API_KEY",
    chat_completions_path="/chat/completions",
    models_path="/models",
    system_prompt_files=[],
    temperature=0.0,
    max_completion_tokens=1,
    max_attempts=2,
    max_tool_calls=2,
    lean_checks_amount=2,
    headers={},
    header_envs={},
    env_contract={"required": [], "optional": []},
    extra_body={},
    request_timeout_seconds=1,
    command=[],
)

responses = iter([
    {
        "choices": [
            {
                "message": {
                    "content": "",
                    "tool_calls": [
                        {
                            "id": "call-1",
                            "type": "function",
                            "function": {"name": "run_lean_check", "arguments": "{}"},
                        }
                    ],
                }
            }
        ]
    },
    {"choices": [{"message": {"content": ""}}]},
])
original_send = default_agent.send_chat_completion
original_execute_tool = default_agent.TaskProofRuntime.execute_tool
original_evaluate = default_agent.TaskProofRuntime.evaluate_current
default_agent.send_chat_completion = lambda *_args, **_kwargs: next(responses)
default_agent.TaskProofRuntime.execute_tool = lambda self, name, arguments: {
    "status": "passed" if name == "run_lean_check" else "ok",
    "failure_mode": None,
    "details": "",
}
default_agent.TaskProofRuntime.evaluate_current = lambda self, **_kwargs: {
    "status": "passed",
    "failure_mode": None,
    "details": "",
}
try:
    _, _, _, evaluation, attempts, _ = execute_interactive_agent_task(config, task, build_messages(config, task))
finally:
    default_agent.send_chat_completion = original_send
    default_agent.TaskProofRuntime.execute_tool = original_execute_tool
    default_agent.TaskProofRuntime.evaluate_current = original_evaluate

if evaluation.get("status") != "passed":
    raise SystemExit(f"expected finalize after a passing lean check, got {evaluation!r}")
if attempts[-1].get("missing_required_tool_use"):
    raise SystemExit("passing run_lean_check should satisfy lean_checks_amount early")
PY
python3 harness/default_agent.py describe --profile "$DEFAULT_AGENT_PROFILE"
python3 harness/default_agent.py describe --profile "$CUSTOM_AGENT_PROFILE"
python3 harness/default_agent.py describe --profile openai-proxy-fast
python3 harness/default_agent.py describe --config harness/default-agent.example.json

if [[ "$RUN_LIVE_AGENT_CHECKS" == "1" && -n "${VERITY_BENCHMARK_AGENT_API_KEY:-}" ]]; then
  python3 harness/default_agent.py probe --profile "$DEFAULT_AGENT_PROFILE" --ensure-model
  python3 harness/default_agent.py probe --profile openai-proxy-fast --ensure-model
  python3 harness/agent_runner.py run ethereum/deposit_contract_minimal/deposit_count --profile "$DEFAULT_AGENT_PROFILE"
  python3 harness/agent_runner.py run ethereum/deposit_contract_minimal/deposit_count --profile openai-proxy-fast
fi

if [[ "$RUN_LIVE_AGENT_CHECKS" == "1" && -n "${VERITY_BENCHMARK_AGENT_BASE_URL:-}" && -n "${VERITY_BENCHMARK_AGENT_MODEL:-}" && -n "${VERITY_BENCHMARK_AGENT_API_KEY:-}" ]]; then
  python3 harness/default_agent.py probe --profile "$CUSTOM_AGENT_PROFILE" --ensure-model
  python3 harness/agent_runner.py run ethereum/deposit_contract_minimal/deposit_count --profile "$CUSTOM_AGENT_PROFILE"
  python3 harness/agent_runner.py run ethereum/deposit_contract_minimal/deposit_count --config harness/default-agent.example.json
fi

python3 scripts/validate_manifests.py
python3 scripts/generate_metadata.py
./scripts/run_all.sh
