# Task Harness

This directory holds the fixed-harness scaffold for task-oriented benchmark execution.

Execution is centered on a single task at a time. The task manifest is the execution
contract, and the runner consumes its explicit proof target instead of deriving the
public benchmark interface from case-level conventions.

The shell entrypoints in `scripts/` delegate to `harness/task_runner.py`.

The default benchmark agent now has its own explicit entrypoint:

- `scripts/run_default_agent.sh <task_ref>` invokes the default-agent runner for one task
- `scripts/run_default_agent_case.sh <project/case_id>` invokes the same path for each task in one case
- `scripts/run_default_agent_all.sh` invokes the same path for all active tasks
- `scripts/run_custom_agent.sh <task_ref>` invokes the same runner on the custom-agent track
- `scripts/run_custom_agent_case.sh <project/case_id>` invokes the custom-agent track for each task in one case
- `scripts/run_custom_agent_all.sh` invokes the custom-agent track for all active tasks
- `harness/agent_runner.py` is the first-class runner for task, case, and suite default-agent execution
- bundled reusable profiles live in `harness/agents/*.json`
- `benchmark.toml` publishes the benchmark-owned profile defaults: `default` for the repo reference track and `openai-compatible` for the custom/external track
- the default profile is `default`, which is the repo-owned reference benchmark agent identity on the `reference/default` run path
- the generic external profile is `openai-compatible`, which is the baseline `custom/openai-compatible` run path
- the direct proxy profile is `openai-proxy-fast`, which is a pinned `custom/openai-proxy-fast` run path
- the current transport adapter contract is `openai_compatible`
- credentials and endpoint selection are injected through env vars where the profile does not pin them
- each connection field is explicit in config: `base_url`, `model`, and `api_key` may be pinned directly or sourced from `*_env`
- the default-agent run artifact is schema-backed by `schemas/agent-run.schema.json`
- each run artifact records the resolved `base_url` and `model` plus the originating `*_env` contract for reproducibility
- task artifacts are partitioned under `results/agent_runs/<track>/<run_slug>/...`
- aggregated case/suite agent-run status is written to `results/agent_summaries/<track>/<run_slug>.json`
- compatibility aliases remain at `results/agent_runs/*.json` and `results/agent_summary.json` for the repo reference `default` profile
- `harness/agent_runner.py` resolves one `ResolvedAgentConfig` per run scope and reuses it across tasks, so missing or bad required env config fails once up front for live runs

Default OpenAI-compatible env contract:

- `VERITY_BENCHMARK_AGENT_BASE_URL`
- `VERITY_BENCHMARK_AGENT_MODEL`
- `VERITY_BENCHMARK_AGENT_API_KEY`

Bundled profile contract:

- `default`: repo-owned default benchmark agent; pins base URL to `https://agent-backend.thomas.md/v1` and model to `builtin/fast`, and only requires `VERITY_BENCHMARK_AGENT_API_KEY`
- `openai-compatible`: generic external OpenAI-compatible backend; expects all three env vars above
- `openai-proxy-fast`: direct pinned proxy profile for `https://agent-backend.thomas.md/v1` and `builtin/fast`; only requires `VERITY_BENCHMARK_AGENT_API_KEY`

Safe reuse paths through the same default-agent entrypoints:

- keep the repo-owned reference run path: `./scripts/run_default_agent.sh <task_ref>` with the bundled `default` profile
- switch the same entrypoint onto the generic external profile: `VERITY_BENCHMARK_AGENT_PROFILE=openai-compatible ./scripts/run_default_agent.sh <task_ref>`
- reuse the repo-owned backend through the external contract: `VERITY_BENCHMARK_AGENT_BASE_URL=https://agent-backend.thomas.md/v1 VERITY_BENCHMARK_AGENT_MODEL=builtin/fast VERITY_BENCHMARK_AGENT_API_KEY=... VERITY_BENCHMARK_AGENT_PROFILE=openai-compatible ./scripts/run_default_agent.sh <task_ref>`
- keep a repo-local custom config on the same runner: `VERITY_BENCHMARK_AGENT_CONFIG=harness/default-agent.example.json ./scripts/run_default_agent.sh <task_ref>`
- inspect which env vars a profile or config expects with `python3 harness/default_agent.py describe --profile <name>` or `--config <path>`

Optional config-only extensions for OpenAI-compatible backends:

- `models_path`: model-discovery path used by `probe`
- `header_envs`: map of HTTP header name to env var for proxy-specific auth/routing
- `extra_body`: extra JSON merged into the chat-completions request body
- `request_timeout_seconds`: request timeout for both probe and run

Useful commands:

- `python3 harness/agent_runner.py list --suite active`
- `python3 harness/default_agent.py profiles`
- `python3 harness/default_agent.py validate-config harness/agents/default.json`
- `python3 harness/default_agent.py validate-config harness/agents/openai-compatible.json`
- `python3 harness/default_agent.py validate-config harness/agents/openai-proxy-fast.json`
- `python3 harness/default_agent.py validate-config harness/default-agent.example.json`
- `python3 harness/default_agent.py describe --profile default`
- `python3 harness/default_agent.py describe --profile openai-compatible`
- `python3 harness/default_agent.py describe --profile openai-proxy-fast`
- `python3 harness/default_agent.py describe --config harness/default-agent.example.json`
- `python3 harness/default_agent.py probe --profile openai-proxy-fast --ensure-model`
- `VERITY_BENCHMARK_AGENT_API_KEY=... python3 harness/default_agent.py probe --profile openai-proxy-fast --ensure-model`
- `VERITY_BENCHMARK_AGENT_API_KEY=... python3 harness/agent_runner.py run-case ethereum/deposit_contract_minimal --profile default`
- `python3 harness/default_agent.py prompt ethereum/deposit_contract_minimal/deposit_count --profile default`
- `./scripts/run_default_agent.sh ethereum/deposit_contract_minimal/deposit_count`
- `VERITY_BENCHMARK_AGENT_PROFILE=openai-compatible ./scripts/run_default_agent.sh ethereum/deposit_contract_minimal/deposit_count`
- `VERITY_BENCHMARK_AGENT_BASE_URL=https://agent-backend.thomas.md/v1 VERITY_BENCHMARK_AGENT_MODEL=builtin/fast VERITY_BENCHMARK_AGENT_API_KEY=... VERITY_BENCHMARK_AGENT_PROFILE=openai-compatible ./scripts/run_default_agent.sh ethereum/deposit_contract_minimal/deposit_count`
- `VERITY_BENCHMARK_AGENT_BASE_URL=https://agent-backend.thomas.md/v1 VERITY_BENCHMARK_AGENT_MODEL=builtin/fast VERITY_BENCHMARK_AGENT_API_KEY=... ./scripts/run_custom_agent.sh ethereum/deposit_contract_minimal/deposit_count`
- `VERITY_BENCHMARK_AGENT_CONFIG=harness/default-agent.example.json ./scripts/run_default_agent.sh ethereum/deposit_contract_minimal/deposit_count`
- `./scripts/run_custom_agent.sh ethereum/deposit_contract_minimal/deposit_count`
- `./scripts/run_default_agent_case.sh ethereum/deposit_contract_minimal`
- `./scripts/run_custom_agent_case.sh ethereum/deposit_contract_minimal`
- `./scripts/run_default_agent_all.sh`
- `./scripts/run_custom_agent_all.sh`

Supported task manifest interface fields:

- `source_ref`: pinned upstream source reference for reproducibility
- `task_interface_version`: version of the task execution contract
- `proof_target`: Lean module target for the task proof surface
- `evaluation_engine`: currently `lean_build`
- `evaluation_target`: the module passed to `lake build`
- `evaluation_declaration`: declaration that must exist on the proof target

`case.yaml` still carries curation and provenance metadata, but it is no longer the
canonical description of how a task is executed.

Config contract for OpenAI-compatible backends:

- set `base_url`, `model`, and `api_key` directly when you want a pinned reusable profile
- set `base_url_env`, `model_env`, and `api_key_env` when those values should come from the environment
- for each of the three connection fields, the config must provide either the direct value or the env var name
- bundled pinned profiles use `null` for unused `*_env` fields instead of placeholder empty strings
