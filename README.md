# verity-benchmark

Reproducible benchmark scaffold for evaluating Verity-based specification and proof workflows on real protocol slices. The repository is task-oriented: cases curate translated artifacts, while tasks define the benchmark API, evaluation unit, and explicit execution contract for concrete invariants or specifications.

This repository pins:
- Lean toolchain: `leanprover/lean4:v4.22.0`
- Verity dependency: `Th0rgal/verity@4ebe4931d25e5a1594fcd3f43ff040ecc3c4225a`

Current status:
- Active `cases/`: 4 concrete benchmark cases
- Active `tasks/`: 14 concrete benchmark tasks
- Buildable active cases: 4
- Non-buildable active cases: 0
- `backlog/`: placeholder intake entries kept visible without polluting the active suite

Repository layout:
- `Benchmark/`: canonical Lean modules that must compile under `lake build`
- `families/`: family and implementation manifests for benchmark source organization
- `cases/`: active benchmark cases with canonical `case.yaml` manifests and `tasks/*.yaml` benchmark units
- `backlog/`: non-runnable placeholders and intake candidates
- `harness/`: fixed-harness scaffold and task runner
- `schemas/`: machine-readable schemas for manifests and run results
- `benchmark-inventory.json`: generated machine-readable inventory
- `REPORT.md`: generated status report
- `results/`: JSON outputs emitted by the runner scripts
- `scripts/generate_metadata.py`: regenerates the inventory and report from manifests
- `scripts/validate_manifests.py`: validates manifest YAML against the repository schemas
- `scripts/run_task.sh`: agent entrypoint for one benchmark task
- `scripts/run_case.sh`: agent entrypoint for one case
- `scripts/run_all.sh`: agent entrypoint for all active tasks
- `scripts/run_default_agent.sh`: explicit default-agent entrypoint for one task
- `scripts/run_default_agent_case.sh`: explicit default-agent entrypoint for one case
- `scripts/run_default_agent_all.sh`: explicit default-agent entrypoint for all active tasks
- `scripts/check.sh`: repo-level metadata and benchmark check
- `docs/architecture/task-api.md`: benchmark architecture note for case/task/source roles
- `schemas/agent-run.schema.json`: schema for default-agent run artifacts

Design choices:
- One folder per benchmark case, with many tasks per case as the intended scaling unit
- Families and implementations are tracked explicitly so source provenance stays stable even as case slices evolve
- Each task declares its own evaluation contract instead of relying on runner inference
- Pinned `source_ref` values are the reproducibility unit; local paths are supporting metadata
- Tasks can target either a spec declaration or an explicit proof module/declaration
- The default-agent path is adapter-driven and uses the `openai_compatible` contract for both the repo-default setup and external backends
- The default-agent path uses named profiles in `harness/agents/` so the repo-owned default agent and external OpenAI-compatible backends share one entrypoint
- The default-agent path is now runner-backed at task, case, and suite scope through `harness/agent_runner.py`
- The default-agent config contract supports both pinned JSON values and env-injected values, and the harness can now report the resolved wiring explicitly
- One selected contract per project unless scope is still ambiguous
- The active suite is still mostly spec-oriented, but proof manifests now support and exercise explicit proof targets
- `case.yaml` plus `tasks/*.yaml` are the source of truth for benchmark state
- Stages are intentionally small: `candidate`, `scoped`, `build_green`, `proof_partial`, `proof_complete`
- `build_green` means the Verity slice typechecks today; it does not mean the case is fully proved
- Abstractions and unsupported features are documented explicitly so later papers can reason about abstraction debt and blocked coverage

Manifest model:
- `families/<family>/family.yaml`: semantic grouping and source-language coverage
- `families/<family>/implementations/<impl>/implementation.yaml`: pinned upstream implementation metadata
- `cases/<project>/<case>/case.yaml`: translated slice status, provenance, abstraction metadata, and pinned `source_ref`
- `cases/<project>/<case>/tasks/*.yaml`: scored task unit with property class, task interface, artifacts in scope, and explicit evaluation target

Architecture note:

- [`docs/architecture/task-api.md`](/workspaces/mission-199bf89a/repo/docs/architecture/task-api.md)

Regenerate metadata:

```bash
python3 scripts/generate_metadata.py
```

Run one case:

```bash
./scripts/run_case.sh ethereum/deposit_contract_minimal
```

Run one task:

```bash
./scripts/run_task.sh ethereum/deposit_contract_minimal/deposit_count
```

Run the default benchmark agent for one task:

```bash
export VERITY_BENCHMARK_AGENT_API_KEY="<redacted>"
python3 harness/default_agent.py profiles
python3 harness/default_agent.py describe --profile openai-proxy-fast
python3 harness/default_agent.py probe --profile default --ensure-model
./scripts/run_default_agent.sh ethereum/deposit_contract_minimal/deposit_count
```

Run the default benchmark agent for one case or the whole active suite:

```bash
export VERITY_BENCHMARK_AGENT_API_KEY="<redacted>"
./scripts/run_default_agent_case.sh ethereum/deposit_contract_minimal
./scripts/run_default_agent_all.sh
```

Bundled default-agent profiles:

- `default`: repo-owned default benchmark agent, pinned to `https://agent-backend.thomas.md/v1` and `builtin/fast`; provide `VERITY_BENCHMARK_AGENT_API_KEY`
- `openai-compatible`: generic external OpenAI-compatible profile; provide `VERITY_BENCHMARK_AGENT_BASE_URL`, `VERITY_BENCHMARK_AGENT_MODEL`, and `VERITY_BENCHMARK_AGENT_API_KEY`
- `openai-proxy-fast`: direct pinned proxy profile for `https://agent-backend.thomas.md/v1` and `builtin/fast`; provide `VERITY_BENCHMARK_AGENT_API_KEY`

Exact proxy/model wiring supported through the shared default-agent path:

```bash
export VERITY_BENCHMARK_AGENT_API_KEY="sk-proxy-898b52c81ce84c2aa4f9bb8f6fb10984"
VERITY_BENCHMARK_AGENT_PROFILE=openai-proxy-fast \
  ./scripts/run_default_agent.sh ethereum/deposit_contract_minimal/deposit_count
```

Generic external OpenAI-compatible wiring through the same path:

```bash
export VERITY_BENCHMARK_AGENT_BASE_URL="https://agent-backend.thomas.md/v1"
export VERITY_BENCHMARK_AGENT_MODEL="builtin/fast"
export VERITY_BENCHMARK_AGENT_API_KEY="sk-proxy-898b52c81ce84c2aa4f9bb8f6fb10984"
VERITY_BENCHMARK_AGENT_PROFILE=openai-compatible \
  ./scripts/run_default_agent.sh ethereum/deposit_contract_minimal/deposit_count
```

`python3 harness/default_agent.py describe --profile <name>` prints the resolved OpenAI-compatible contract, where each field came from, and which env vars are still required.

Run all active tasks:

```bash
./scripts/run_all.sh
```

Check metadata and all runnable cases:

```bash
./scripts/check.sh
```
