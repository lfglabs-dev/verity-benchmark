# Harness Prompt

Each task gives the agent:
- fixed implementation files
- fixed specification files
- one editable proof file
- one theorem target

The agent must return the full proof file. It must not change specs, change implementations, or rely on hidden solved proofs.

The harness rejects placeholders, runs Lean in a temp workspace, and checks the target theorem.
