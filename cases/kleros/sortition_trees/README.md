# sortition_trees

Selected from `kleros/kleros-v2` at `75125dfa54eee723cac239f20e5746d15786196b`.

What is selected:
- Library: `contracts/src/libraries/SortitionTrees.sol`
- Functions: `set`, `updateParents`, `draw`
- Benchmark focus: additive tree invariants, draw intervals, and ID/index consistency

Frozen specs:
- each parent equals the sum of its children
- the root equals the sum of all leaves
- draw intervals match leaf weights
- every successful draw resolves to a valid leaf node index
- `IDsToNodeIndexes` and `nodeIndexesToIDs` remain aligned

Intentionally left out:
- dynamic arrays and arbitrary branching factor `K`
- bytes32 packing and unpacking details
- hash-based ticket derivation
- vacancy-stack management
