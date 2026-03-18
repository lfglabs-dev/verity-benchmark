# Contributing

The repository is optimized for small, deterministic benchmark updates.

## Case contract

Each case is defined by a single canonical manifest at `cases/<project>/<case_id>/case.yaml` or `backlog/<project>/<case_id>/case.yaml`.

Required keys:
- `project`
- `case_id`
- `schema_version`
- `stage`
- `selected_functions`
- `source_language`
- `verity_version`
- `lean_toolchain`
- `notes`

Optional but recommended keys:
- `lean_target`
- `upstream_repo`
- `upstream_commit`
- `original_contract_path`
- `failure_reason`

## Stage meanings

- `candidate`: intake or placeholder entry, not part of the active suite
- `scoped`: concrete target is pinned but not yet runnable
- `build_green`: Verity translation compiles under the pinned toolchain
- `proof_partial`: compileable case with partial proof coverage
- `proof_complete`: compileable case with full intended proof coverage

## Workflow

1. Edit or add the case manifest.
2. Run `python3 scripts/generate_metadata.py`.
3. If the case is runnable, run `./scripts/run_case.sh <project/case_id>`.
4. Run `./scripts/check.sh` before opening a PR.

Do not edit `benchmark-inventory.json` or `REPORT.md` by hand. They are generated from the manifests.
