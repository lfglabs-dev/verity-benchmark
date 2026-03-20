# Task API Architecture Note

## Benchmark contract

Each benchmark task is now a strict proof-generation unit:

- Input to the agent: a fixed Verity implementation, a fixed Lean specification, and one editable Lean proof template.
- Output from the agent: the complete contents of that single editable Lean proof file.
- Pass/fail: machine-checked by writing the returned file into a temp workspace, rejecting obvious placeholders, compiling it with Lean, and checking the target theorem declaration exists.

The benchmark does not ask the agent to invent specs, modify implementations, or inspect hidden solved proofs.

## Repository layout

- `Benchmark/Cases/...`: canonical solved Lean modules kept in the main package build. These remain the hidden reference solutions used for solvability checks and repository maintenance.
- `Benchmark/Generated/<Family>/<Case>/Tasks/<Task>.lean`: public unsolved proof templates. These are valid package-path modules, but `lakefile.lean` does not import `Benchmark.Generated`, so the main package build stays solution-only.
- `cases/*/*/tasks/*.yaml`: public task manifests. They point to the implementation files, specification files, editable proof template, explicit theorem target, and proof-family label.

## Task manifest fields

The public task API is the manifest. Each task declares:

- `implementation_files`: fixed Lean implementation context for the task
- `specification_files`: fixed Lean theorem/specification context
- `editable_files`: the single agent-editable Lean proof file
- `theorem_name`: the explicit theorem declaration that must exist after evaluation
- `proof_family`: one of the benchmark’s five proof families

The repository also keeps hidden maintenance metadata in the same manifest:

- `reference_solution_module`
- `reference_solution_declaration`

These fields support separate validation of the hidden solved modules without exposing any proof body in the public benchmark surface.

## Proof-family taxonomy

The benchmark uses five coarse proof families:

- `functional_correctness`: implementation output or post-state matches the stated spec
- `state_preservation_local_effects`: only the intended state changes occur and preserved fields remain stable
- `authorization_enablement`: successful execution implies the required guards or permissions
- `protocol_transition_correctness`: state transitions follow the protocol’s phase or threshold rules
- `refinement_equivalence`: the implementation refines an abstract spec or preserves an equivalence

## Evaluation split

Two checks are intentionally separate:

- Reference-solution validation: `harness/task_runner.py` builds the hidden `Benchmark/Cases/...` module and checks the reference theorem exists.
- Candidate-proof evaluation: `harness/default_agent.py` evaluates the agent’s returned editable file against the public task contract.

This preserves a clean public benchmark interface while keeping hidden solvability checks available for repo maintenance.
