#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
python3 harness/default_agent.py profiles
python3 harness/default_agent.py validate-config harness/agents/default.json
python3 harness/default_agent.py validate-config harness/agents/openai-compatible.json
python3 harness/default_agent.py validate-config harness/agents/openai-proxy-fast.json
python3 harness/default_agent.py validate-config harness/default-agent.example.json
python3 harness/agent_runner.py run ethereum/deposit_contract_minimal/deposit_count --profile default --dry-run
python3 harness/agent_runner.py run-case ethereum/deposit_contract_minimal --profile default --dry-run
python3 harness/agent_runner.py run ethereum/deposit_contract_minimal/deposit_count --profile openai-compatible --dry-run
python3 harness/agent_runner.py run ethereum/deposit_contract_minimal/deposit_count --config harness/default-agent.example.json --dry-run
python3 harness/default_agent.py describe --profile default
python3 harness/default_agent.py describe --profile openai-compatible
python3 harness/default_agent.py describe --config harness/default-agent.example.json
python3 scripts/validate_manifests.py
python3 scripts/generate_metadata.py
./scripts/run_all.sh
