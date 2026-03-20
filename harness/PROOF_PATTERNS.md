# Proof Patterns

Use public operational proof patterns, not hidden case solutions.

Verity execution proofs often reduce with `simp` once the execution path is fixed.
Typical symbols to unfold or simplify are:

- `getStorage`, `setStorage`, `setMapping`, `setMappingUint`
- `Verity.require`, `Verity.bind`, `Bind.bind`
- `Verity.pure`, `Pure.pure`
- `Contract.run`, `ContractResult.snd`
- the contract's storage labels, such as `ContractName.counter`

Common pattern for a successful-path slot-write theorem:

```lean
private theorem slot_write_helper
    (x : Uint256) (s : ContractState)
    (hGuard : ...) :
    let s' := ((ContractName.fn x).run s).snd
    s'.storage slot = expected := by
  simp [ContractName.fn, hGuard, ContractName.slotField,
    getStorage, setStorage, Verity.require, Verity.bind, Bind.bind,
    Verity.pure, Pure.pure, Contract.run, ContractResult.snd]
```

Common pattern for a branch theorem:

```lean
by_cases hBranch : condition
· simp [ContractName.fn, hBranch, ...]
· have hNotBranch : ¬ condition := hBranch
  simp [ContractName.fn, hNotBranch, ...]
```

Do not use `split` on the final post-state goal unless the goal itself is explicitly a conjunction or a sum-type elimination. Generated Verity execution terms often simplify better if you first prove the exact branch facts used by the contract and then call `simp`.

For arithmetic threshold branches, the negated fact often needs to be restated in the comparator form used by the generated code. Example:

```lean
have hNotFull : ¬ 32000000000 ≤ depositAmount := Nat.not_le_of_lt hSmall
simp [ContractName.fn, hCount, hMin, hNotFull, ...]
```

If one theorem has to work for both sides of a branch, prove two private helpers first, one per branch, then use `by_cases` in the public theorem and `simpa using` the matching helper.

If `simp` reduces the goal to concrete slot equalities or a finite `if` over concrete slot numbers, `native_decide` or `decide` often closes the remaining goal.

Typical shape:

```lean
have hSlot : s'.storage slot = expected := by
  simp [ContractName.fn, hGuard, ...]
  native_decide
```

If `simp` already solves the goal, do not leave a trailing `decide`, `exact`, or extra tactic line after it; Lean will report `no goals to be solved`.

If the public theorem is just a named spec, it is often cleaner to:

1. prove a private helper theorem about the concrete post-state slots,
2. unfold the spec,
3. finish with `simpa using ...`.
