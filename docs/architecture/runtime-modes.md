# Benchmark Runtime Modes

The benchmark runtime supports three interaction modes over the same task contract.

## `strict`

- Fixed public input: `implementation_files`, `specification_files`, one `editable_files` proof template
- Agent output: a complete replacement for the editable Lean proof file
- Harness loop: bounded propose-check-repair rounds with Lean checker feedback
- Purpose: pure proof-synthesis baseline

## `interactive`

- Same task contract and evaluator as `strict`
- Adds a small task-scoped tool surface:
  - `read_public_file`
  - `write_editable_proof`
  - `run_lean_check`
  - `inspect_lean_goals`
  - `search_public_defs`
- Purpose: measure Lean proof engineering with minimal local proof tools

## `custom`

- The benchmark still owns task format, file allowlist, and final evaluation
- An external agent system is invoked through a command adapter protocol
- The adapter receives:
  - task metadata
  - structured `public_files` contents
  - the editable file path
  - the rendered system/user prompt bundle
- The adapter returns a final candidate proof file, which the benchmark evaluates independently

This keeps the benchmark comparable while still allowing external systems such as OpenGauss to be tested through a narrow integration contract instead of replacing the benchmark runtime.
