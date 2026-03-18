#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
DEFAULT_AGENT_PROFILE="$(python3 -c 'import tomllib; print(tomllib.load(open("benchmark.toml", "rb"))["default_agent_default_profile"])')"
CUSTOM_AGENT_PROFILE="$(python3 -c 'import tomllib; print(tomllib.load(open("benchmark.toml", "rb"))["custom_agent_default_profile"])')"

python3 harness/default_agent.py profiles
python3 harness/default_agent.py validate-config "harness/agents/${DEFAULT_AGENT_PROFILE}.json"
python3 harness/default_agent.py validate-config "harness/agents/${CUSTOM_AGENT_PROFILE}.json"
python3 harness/default_agent.py validate-config harness/agents/openai-proxy-fast.json
python3 harness/default_agent.py validate-config harness/default-agent.example.json
python3 harness/default_agent.py validate-config "$(pwd)/harness/default-agent.example.json"
python3 harness/agent_runner.py run ethereum/deposit_contract_minimal/deposit_count --profile "$DEFAULT_AGENT_PROFILE" --dry-run
python3 harness/agent_runner.py run-case ethereum/deposit_contract_minimal --profile "$DEFAULT_AGENT_PROFILE" --dry-run
python3 harness/agent_runner.py run ethereum/deposit_contract_minimal/deposit_count --profile "$CUSTOM_AGENT_PROFILE" --dry-run
python3 harness/agent_runner.py run ethereum/deposit_contract_minimal/deposit_count --profile openai-proxy-fast --dry-run
python3 harness/agent_runner.py run ethereum/deposit_contract_minimal/deposit_count --config harness/default-agent.example.json --dry-run
python3 - <<'PY'
from pathlib import Path
import tomllib

root = Path(".")
config = tomllib.loads((root / "benchmark.toml").read_text(encoding="utf-8"))
expected = [
    config["default_agent_summary"],
    config["custom_agent_summary"],
    "results/agent_summaries/custom/openai-proxy-fast.json",
    "results/agent_summaries/custom/custom-openai-compatible.json",
]
missing = [path for path in expected if not (root / path).is_file()]
if missing:
    raise SystemExit(f"missing expected agent summary artifacts: {', '.join(missing)}")
PY
python3 - <<'PY'
from pathlib import Path
import sys

sys.path.insert(0, str(Path("harness").resolve()))

from default_agent import ResolvedAgentConfig, ensure_configured_model_available

config = ResolvedAgentConfig(
    profile="test",
    agent_id="agent",
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
    headers={},
    header_envs={},
    env_contract={"required": [], "optional": []},
    extra_body={},
    request_timeout_seconds=1,
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
python3 harness/default_agent.py describe --profile "$DEFAULT_AGENT_PROFILE"
python3 harness/default_agent.py describe --profile "$CUSTOM_AGENT_PROFILE"
python3 harness/default_agent.py describe --profile openai-proxy-fast
python3 harness/default_agent.py describe --config harness/default-agent.example.json

if [[ -n "${VERITY_BENCHMARK_AGENT_API_KEY:-}" ]]; then
  python3 harness/default_agent.py probe --profile "$DEFAULT_AGENT_PROFILE" --ensure-model
  python3 harness/default_agent.py probe --profile openai-proxy-fast --ensure-model
  python3 harness/agent_runner.py run ethereum/deposit_contract_minimal/deposit_count --profile "$DEFAULT_AGENT_PROFILE"
  python3 harness/agent_runner.py run ethereum/deposit_contract_minimal/deposit_count --profile openai-proxy-fast
fi

if [[ -n "${VERITY_BENCHMARK_AGENT_BASE_URL:-}" && -n "${VERITY_BENCHMARK_AGENT_MODEL:-}" && -n "${VERITY_BENCHMARK_AGENT_API_KEY:-}" ]]; then
  python3 harness/default_agent.py probe --profile "$CUSTOM_AGENT_PROFILE" --ensure-model
  python3 harness/agent_runner.py run ethereum/deposit_contract_minimal/deposit_count --profile "$CUSTOM_AGENT_PROFILE"
  python3 harness/agent_runner.py run ethereum/deposit_contract_minimal/deposit_count --config harness/default-agent.example.json
fi

python3 scripts/validate_manifests.py
python3 scripts/generate_metadata.py
./scripts/run_all.sh
