# verity-benchmark

Benchmark for Verity-based Lean proofs on small slices of real contracts.

The repo separates:
- `Benchmark/Cases/`: hidden solved proofs used to keep tasks maintainable
- `Benchmark/Generated/`: public unsolved proof templates
- `cases/`: active benchmark cases and task manifests
- `backlog/`: placeholders that are not runnable
- `harness/`: runner and agent integration
- `results/`: run artifacts

Current active suite:
- 4 cases
- 18 tasks
- 4 buildable cases

The task contract is strict:
- fixed implementation files
- fixed specification files
- one editable proof file
- one required theorem

The agent must return the full editable proof file. The harness rejects placeholders, runs Lean in a temp workspace, and checks the theorem exists.

Useful commands:

```bash
python3 scripts/generate_metadata.py
python3 scripts/validate_manifests.py
./scripts/check.sh
./scripts/run_task.sh ethereum/deposit_contract_minimal/deposit_count
./scripts/run_case.sh ethereum/deposit_contract_minimal
./scripts/run_all.sh
```

Default agent:

```bash
python3 harness/default_agent.py profiles
python3 harness/default_agent.py describe --profile default
./scripts/run_default_agent.sh ethereum/deposit_contract_minimal/deposit_count
./scripts/run_default_agent_case.sh ethereum/deposit_contract_minimal
./scripts/run_default_agent_all.sh
```

Custom OpenAI-compatible agent:

```bash
python3 harness/default_agent.py describe --profile openai-compatible
./scripts/run_custom_agent.sh ethereum/deposit_contract_minimal/deposit_count
./scripts/run_custom_agent_case.sh ethereum/deposit_contract_minimal
./scripts/run_custom_agent_all.sh
```

Benchmark matrix:

```bash
python3 scripts/run_benchmark_matrix.py start
python3 scripts/run_benchmark_matrix.py status
python3 scripts/run_benchmark_matrix.py logs --target-key builtin-fast
python3 scripts/run_benchmark_matrix.py pause --target-key builtin-fast
python3 scripts/run_benchmark_matrix.py resume --target-key builtin-fast
python3 scripts/run_benchmark_matrix.py wait
```

Env handling:
- `.env` is committed in encrypted `dotenvx` form
- `.env.keys` is local-only and gitignored
- CI uses the `DOTENV_PRIVATE_KEY` secret
- `.env.local` can override values locally

Live backend checks are off by default. Set `VERITY_BENCHMARK_RUN_LIVE_AGENT_CHECKS=1` to enable them in `./scripts/check.sh`.

More detail:
- [`harness/README.md`](./harness/README.md)
- [`docs/architecture/task-api.md`](./docs/architecture/task-api.md)
- [`docs/architecture/runtime-modes.md`](./docs/architecture/runtime-modes.md)

<!-- BENCHMARK_MATRIX:START -->
## Benchmark Results

Run `python3 scripts/run_benchmark_matrix.py render` after the matrix finishes to refresh this section.
<!-- BENCHMARK_MATRIX:END -->
