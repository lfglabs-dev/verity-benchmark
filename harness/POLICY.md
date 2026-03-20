# Harness Policy

- `tasks/*.yaml` is the execution unit.
- The task manifest defines the proof contract.
- Only run tasks with `proof_status` `partial` or `complete`.
- Write deterministic outputs under `results/tasks/`.
