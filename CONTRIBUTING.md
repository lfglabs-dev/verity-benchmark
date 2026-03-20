# Contributing

Keep changes small and deterministic.

Case source of truth:
- `cases/<project>/<case>/case.yaml` for active cases
- `backlog/<project>/<case>/case.yaml` for placeholders

Stages:
- `candidate`: intake only
- `scoped`: target pinned, not runnable
- `build_green`: translation builds
- `proof_partial`: some proofs done
- `proof_complete`: intended proofs done

Workflow:
1. Edit the manifest or task files.
2. Run `python3 scripts/generate_metadata.py`.
3. Run `./scripts/run_case.sh <project/case>` if the case is runnable.
4. Run `./scripts/check.sh`.

Do not edit `benchmark-inventory.json` or `REPORT.md` by hand.
