You are doing a deep-search research pass for the Verity benchmark.

Goal:
Find 5-10 public smart contract or programming challenge candidates that would meaningfully expand benchmark coverage, with emphasis on challenge classes that are not already represented by the current suite.

Current benchmark coverage to treat as already represented:
- Monotonic counters and threshold activation
- Claim-accounting conservation and authorization-state updates
- Price computation and bounded storage writes
- Tree conservation, subtree partitioning, and weighted selection

Search requirements:
- Use primary sources only: official repositories, official documentation, whitepapers, audits, standards, or peer-reviewed papers.
- Prefer pinned upstream artifacts with a stable commit, tag, release, or canonical document URL.
- Focus on challenge slices that can be translated into compact proof tasks in Lean/Verity without hardcoding a full protocol.
- Exclude ideas that require private repos, unverifiable folklore, or huge multi-contract environments just to state the property.

For each candidate, return:
1. Title
2. Upstream source URL
3. Exact artifact to pin
4. Challenge class
5. Why it is not covered yet by the current benchmark
6. Minimal benchmark slice to extract
7. 3-5 candidate theorem/task ideas
8. Main proof risks
9. Expected benchmark value for interactive theorem-proving agents

Selection criteria:
- Strong preference for arithmetic invariants, state-machine safety, conservation laws, slippage/rounding bounds, auction logic, liquidation accounting, AMM invariants, rebase/share math, or queue/settlement correctness.
- Prefer contract logic that is widely recognized, reused, and economically meaningful.
- Prefer cases where the interesting reasoning comes from the code path itself, not from giant omitted dependencies.
- Penalize slices that are too trivial, too similar to existing tasks, or too dependent on external cryptography and signatures.

Decision step:
- Rank the candidates.
- Pick exactly one best addition.
- Explain why it beats the next two alternatives.
- Propose a concrete Verity case shape: family id, implementation id, case id, abstraction notes, and initial task list.

Output format:
- A short coverage-gap summary
- A ranked table of candidates
- A final recommendation with explicit source links
- A concrete benchmark-ingestion plan for the chosen addition
