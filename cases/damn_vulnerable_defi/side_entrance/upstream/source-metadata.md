# Upstream metadata

- Repository: https://github.com/OpenZeppelin/damn-vulnerable-defi
- Commit: `master`
- Contract path: `contracts/side-entrance/SideEntranceLenderPool.sol`
- Functions of interest: `deposit`, `flashLoan`, `withdraw`
- Source language: Solidity

Reason for selection:
- canonical flash-loan accounting bug with a direct asset-versus-credit mismatch
- compact enough to encode without callback machinery
- naturally yields both local storage-update tasks and one composed exploit theorem
