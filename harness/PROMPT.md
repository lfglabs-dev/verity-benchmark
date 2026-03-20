# Harness Prompt

The harness assumes a strict proof-generation contract:

- input unit: one benchmark task
- fixed context: `implementation_files` plus `specification_files`
- mutable surface: exactly one file from `editable_files`
- required output: the complete contents of that editable Lean proof file
- allowed iteration: bounded harness-owned propose-check-repair rounds on the same proof file
- disallowed behavior: inventing specs, modifying implementations, or relying on hidden solved proofs
- success criterion: the returned file contains no obvious placeholders, type-checks under Lean in a temp workspace, and defines the declared `theorem_name`

This keeps the benchmark focused on proof construction over fixed translated slices.
