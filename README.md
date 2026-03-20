# verity-benchmark

Reproducible benchmark scaffold for evaluating Verity-based proof workflows on real protocol slices. The repository is task-oriented: cases curate translated artifacts, while tasks define the benchmark API, evaluation unit, and explicit execution contract for concrete invariants.

This repository pins:
- Lean toolchain: `leanprover/lean4:v4.22.0`
- Verity dependency: `Th0rgal/verity@4ebe4931d25e5a1594fcd3f43ff040ecc3c4225a`

Current status:
- Active `cases/`: 4 concrete benchmark cases
- Active `tasks/`: 17 concrete benchmark tasks
- Buildable active cases: 4
- Non-buildable active cases: 0
- `backlog/`: placeholder intake entries kept visible without polluting the active suite

Repository layout:
- `Benchmark/`: canonical solved Lean modules that must compile under `lake build`
- `Benchmark/Generated/`: public unsolved proof templates on Lean-importable paths, intentionally excluded from the main package build
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
- `scripts/run_custom_agent.sh`: custom-agent entrypoint for one task through the same adapter path
- `scripts/run_custom_agent_case.sh`: custom-agent entrypoint for one case through the same adapter path
- `scripts/run_custom_agent_all.sh`: custom-agent entrypoint for all active tasks through the same adapter path
- all six shell wrappers now delegate profile/config resolution to `scripts/run_agent_entrypoint.sh`, so the repo-default and external OpenAI-compatible flows stay on one launcher contract
- `scripts/check.sh`: repo-level metadata and benchmark check
- `docs/architecture/task-api.md`: benchmark architecture note for case/task/source roles
- `schemas/agent-run.schema.json`: schema for default-agent run artifacts

Design choices:
- One folder per benchmark case, with many tasks per case as the intended scaling unit
- Families and implementations are tracked explicitly so source provenance stays stable even as case slices evolve
- Each task declares its own evaluation contract instead of relying on runner inference
- Pinned `source_ref` values are the reproducibility unit; local paths are supporting metadata
- Tasks expose fixed implementation files, fixed specification files, one editable proof file, and an explicit implementation-to-spec theorem target
- Every active task is tagged with one of five proof families: `functional_correctness`, `state_preservation_local_effects`, `authorization_enablement`, `protocol_transition_correctness`, or `refinement_equivalence`
- Hidden reference solutions remain under `Benchmark/Cases/...` for solvability and maintenance checks
- The default-agent path is adapter-driven and uses the `openai_compatible` contract for both the repo-default setup and external backends
- The default-agent path uses named profiles in `harness/agents/` so the repo-owned reference agent and custom OpenAI-compatible backends share one runner
- `benchmark.toml` declares the benchmark-owned defaults: `default_agent_default_profile = "default"` for the repo reference path and `custom_agent_default_profile = "openai-compatible"` for reusable external OpenAI-compatible backends
- The default-agent path is now runner-backed at task, case, and suite scope through `harness/agent_runner.py`
- The OpenAI-compatible connection contract is explicit in config: `base_url`, `model`, and `api_key` can each be pinned directly or supplied via `*_env`
- Default-agent run artifacts preserve both the resolved OpenAI-compatible endpoint/model and the env contract that supplied them
- Default-agent artifacts are partitioned by `track/run_slug` under `results/agent_runs/`, and case/suite summaries are written to `results/agent_summaries/<track>/<run_slug>.json`
- `benchmark.toml` only names the benchmark-owned default summary references: `results/agent_summaries/reference/default.json` and `results/agent_summaries/custom/openai-compatible.json`
- One selected contract per project unless scope is still ambiguous
- The active suite is proof-only at the task level; internal `Specs` modules remain as proof premises inside Lean
- `case.yaml` plus `tasks/*.yaml` are the source of truth for benchmark state
- Stages are intentionally small: `candidate`, `scoped`, `build_green`, `proof_partial`, `proof_complete`
- `build_green` means the Verity slice typechecks today; it does not mean the case is fully proved
- Abstractions and unsupported features are documented explicitly so later papers can reason about abstraction debt and blocked coverage

Manifest model:
- `families/<family>/family.yaml`: semantic grouping and source-language coverage
- `families/<family>/implementations/<impl>/implementation.yaml`: pinned upstream implementation metadata
- `cases/<project>/<case>/case.yaml`: translated slice status, provenance, abstraction metadata, and pinned `source_ref`
- `cases/<project>/<case>/tasks/*.yaml`: scored task unit with public proof-generation inputs plus hidden reference-solution metadata

Architecture note:

- [`docs/architecture/task-api.md`](./docs/architecture/task-api.md)

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
DOTENV_PRIVATE_KEY="<from .env.keys or GitHub secret>" ./scripts/check.sh
python3 harness/default_agent.py profiles
python3 harness/default_agent.py probe --profile default --ensure-model
./scripts/run_default_agent.sh ethereum/deposit_contract_minimal/deposit_count
```

`./scripts/run_default_agent.sh` defaults to the bundled `default` profile from [`benchmark.toml`](./benchmark.toml), which pins `base_url = https://agent-backend.thomas.md/v1` and `model = builtin/fast`; only `VERITY_BENCHMARK_AGENT_API_KEY` must be supplied at runtime.

Encrypted env setup with `dotenvx`:

- The committed [`./.env`](./.env) now holds the OpenAI-compatible benchmark connection values in encrypted form.
- The private decryption key lives in local-only `.env.keys` and in the GitHub repo secret `DOTENV_PRIVATE_KEY`.
- The agent entrypoints and [`./scripts/check.sh`](./scripts/check.sh) auto-load `.env` through `dotenvx` when either `.env.keys` or `DOTENV_PRIVATE_KEY` is present.
- `./scripts/check.sh` stays deterministic by default; live backend probes/runs only happen when `VERITY_BENCHMARK_RUN_LIVE_AGENT_CHECKS=1`.
- `.env.local` stays ignored and can override committed values locally without changing CI.

Run an external OpenAI-compatible backend through the same default-agent entrypoint:

```bash
python3 harness/default_agent.py describe --profile openai-compatible
python3 harness/default_agent.py describe --profile openai-proxy-fast
python3 harness/default_agent.py probe --profile openai-compatible --ensure-model
VERITY_BENCHMARK_AGENT_PROFILE=openai-compatible \
  ./scripts/run_default_agent.sh ethereum/deposit_contract_minimal/deposit_count
VERITY_BENCHMARK_AGENT_PROFILE=openai-proxy-fast \
  ./scripts/run_default_agent.sh ethereum/deposit_contract_minimal/deposit_count
VERITY_BENCHMARK_AGENT_CONFIG=harness/default-agent.example.json \
  ./scripts/run_default_agent.sh ethereum/deposit_contract_minimal/deposit_count
```

`./scripts/run_custom_agent.sh` defaults to the bundled `openai-compatible` profile from [`benchmark.toml`](./benchmark.toml). Reusing the repo-owned backend through that external contract means setting:

```bash
./scripts/run_custom_agent.sh ethereum/deposit_contract_minimal/deposit_count
```

Run the default benchmark agent for one case or the whole active suite:

```bash
./scripts/run_default_agent_case.sh ethereum/deposit_contract_minimal
./scripts/run_default_agent_all.sh
```

Run the custom-agent track through the same adapter path:

```bash
./scripts/run_custom_agent.sh ethereum/deposit_contract_minimal/deposit_count
./scripts/run_custom_agent_case.sh ethereum/deposit_contract_minimal
./scripts/run_custom_agent_all.sh
```

Bundled default-agent profiles:

- `default`: repo-owned reference benchmark agent on `results/agent_runs/reference/default/`; provide `VERITY_BENCHMARK_AGENT_API_KEY`
- `openai-compatible`: generic custom-agent profile on `results/agent_runs/custom/openai-compatible/`; provide `VERITY_BENCHMARK_AGENT_BASE_URL`, `VERITY_BENCHMARK_AGENT_MODEL`, and `VERITY_BENCHMARK_AGENT_API_KEY`
- `openai-proxy-fast`: pinned custom-agent profile on `results/agent_runs/custom/openai-proxy-fast/`; provide `VERITY_BENCHMARK_AGENT_API_KEY`

Use `python3 harness/default_agent.py describe --profile <name>` to inspect the env contract for a bundled profile, or `--config harness/default-agent.example.json` for a repo-local external config.
`--config` accepts either a repo-relative path like `harness/default-agent.example.json` or an absolute JSON config path outside the repo, so external OpenAI-compatible agent definitions can reuse the same runner without being copied under `harness/agents/`.
The repo-owned `default` profile and the reusable `openai-proxy-fast` profile both speak the same `openai_compatible` contract to `https://agent-backend.thomas.md/v1` with `builtin/fast`; the difference is the run track and whether you select them through the benchmark default profile or an explicit external profile/config.
`harness/agent_runner.py` resolves one explicit config per invocation and reuses it across all tasks in that run scope, so live runs fail fast when required env vars such as `base_url`, `model`, or `api_key` are missing or invalid.
`python3 harness/default_agent.py probe --profile <name> --ensure-model` now also fails when `/models` cannot confirm the configured model because the response contains no parseable model ids.
The one-shot default-agent prompt now embeds `implementation_files`, `specification_files`, and the editable proof template, so external OpenAI-compatible backends receive the exact public proof surface through the shared runner.
Live default-agent runs now evaluate the returned proof artifact: the harness writes the candidate file into a temp workspace, rejects `sorry` / `admit` / `axiom`, compiles it with Lean, and checks the declared theorem exists.
Run artifacts now also record `elapsed_seconds` in `schemas/agent-run.schema.json` so live proxy/backend timing is preserved alongside the resolved endpoint and model contract.

Run all active tasks:

```bash
./scripts/run_all.sh
```

Check metadata and all runnable cases:

```bash
./scripts/check.sh
```
