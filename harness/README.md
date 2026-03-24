# Task Harness

The harness runs one task at a time.

Task contract:
- fixed implementation files
- fixed specification files
- one editable proof file
- one theorem name

Main entrypoints:
- `scripts/run_default_agent.sh <task_ref>`
- `scripts/run_default_agent_case.sh <project/case>`
- `scripts/run_default_agent_all.sh`
- `scripts/run_custom_agent.sh <task_ref>`
- `scripts/run_custom_agent_case.sh <project/case>`
- `scripts/run_custom_agent_all.sh`

Core files:
- `harness/agent_runner.py`: task, case, and suite runner
- `harness/default_agent.py`: profile, prompt, probe, and run logic
- `scripts/run_agent_entrypoint.sh`: shared shell launcher
- `harness/agents/*.json`: bundled profiles

Bundled profiles:
- `default`: repo reference profile
- `interactive`: minimal-tool interactive profile
- `openai-compatible`: generic external OpenAI-compatible profile
- `openai-proxy-fast`: pinned proxy profile

Runtime modes:
- `strict`: no agent tools
- `interactive`: small Lean-oriented tool surface
- `custom`: external command adapter, same evaluator

Default OpenAI-compatible env vars:
- `VERITY_BENCHMARK_AGENT_BASE_URL`
- `VERITY_BENCHMARK_AGENT_MODEL`
- `VERITY_BENCHMARK_AGENT_API_KEY`

Env loading:
- `.env` is encrypted with `dotenvx`
- local runs use `.env.keys` or `DOTENV_PRIVATE_KEY`
- CI uses `DOTENV_PRIVATE_KEY`
- `.env.local` is a local override

Useful commands:

```bash
python3 harness/agent_runner.py list --suite active
python3 harness/default_agent.py profiles
python3 harness/default_agent.py describe --profile default
python3 harness/default_agent.py probe --profile default --ensure-model
python3 scripts/analyze_benchmark_run.py attempts results/agent_runs/reference/default/ethereum__deposit_contract_minimal__deposit_count.json
./scripts/run_default_agent.sh ethereum/deposit_contract_minimal/deposit_count
./scripts/run_custom_agent.sh ethereum/deposit_contract_minimal/deposit_count
```
