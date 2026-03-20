# Harness Tools

The fixed harness currently uses only repository-local tools:

- `lake build <target>` for proof-module checks
- `scripts/run_task.sh` for one task
- `scripts/run_all.sh` for sorted task discovery and aggregation

The tool surface is intentionally narrow so later leaderboard runs can pin the same
interaction policy across agents.
