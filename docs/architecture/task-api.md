# Task API

Each task is a proof-generation unit.

Public inputs:
- implementation files
- specification files
- one editable proof file
- one theorem name

Public output:
- the full contents of the editable proof file

Evaluation:
- reject obvious placeholders
- write the file into a temp workspace
- run Lean
- check that the theorem exists

Repo split:
- `Benchmark/Cases/...`: hidden solved proofs for maintenance
- `Benchmark/Generated/...`: public unsolved templates
- `cases/*/*/tasks/*.yaml`: public task manifests

The manifest is the public API. Important fields:
- `implementation_files`
- `specification_files`
- `editable_files`
- `theorem_name`
- `proof_family`

Hidden maintenance fields:
- `reference_solution_module`
- `reference_solution_declaration`
