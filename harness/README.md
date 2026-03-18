# Task Harness

This directory holds the fixed-harness scaffold for task-oriented benchmark execution.

Execution is centered on a single task at a time. The task manifest is the execution
contract, and the runner consumes its explicit evaluation fields instead of deriving the
public benchmark interface from case-level conventions.

Supported evaluation layers:

- translation: build a translated Lean module
- specification: build a spec module and `#check` the declared statement
- proof: build a proof module and `#check` the declared proof/export

The shell entrypoints in `scripts/` delegate to `harness/task_runner.py`.

Supported task manifest interface fields:

- `source_ref`: pinned upstream source reference for reproducibility
- `task_interface_version`: version of the task execution contract
- `spec_target`: Lean module target for the task specification surface
- `proof_target`: Lean module target for the task proof surface when available
- `evaluation_engine`: currently `lean_build`
- `evaluation_target_kind`: one of `translation`, `spec`, `proof`
- `evaluation_target`: the module passed to `lake build`
- `evaluation_declaration`: declaration that must exist for `spec` and `proof` tasks

`case.yaml` still carries curation and provenance metadata, but it is no longer the
canonical description of how a task is executed.
