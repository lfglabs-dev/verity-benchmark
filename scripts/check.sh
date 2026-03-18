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
python3 harness/agent_runner.py run ethereum/deposit_contract_minimal/deposit_count --profile "$DEFAULT_AGENT_PROFILE" --dry-run
python3 harness/agent_runner.py run-case ethereum/deposit_contract_minimal --profile "$DEFAULT_AGENT_PROFILE" --dry-run
python3 harness/agent_runner.py run ethereum/deposit_contract_minimal/deposit_count --profile "$CUSTOM_AGENT_PROFILE" --dry-run
python3 harness/agent_runner.py run ethereum/deposit_contract_minimal/deposit_count --profile openai-proxy-fast --dry-run
python3 harness/agent_runner.py run ethereum/deposit_contract_minimal/deposit_count --config harness/default-agent.example.json --dry-run
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
