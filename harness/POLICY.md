# Harness Policy

- Treat `tasks/*.yaml` as the primary execution unit.
- Preserve case-level compatibility fields because Lean translation targets are still defined per case.
- Only execute a proof target when `proof_status` is `partial` or `complete`.
- Treat the task manifest's explicit proof target as the execution contract.
- Emit deterministic task result paths under `results/tasks/`.
