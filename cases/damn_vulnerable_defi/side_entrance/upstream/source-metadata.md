# Upstream metadata

- Repository: https://github.com/OpenZeppelin/damn-vulnerable-defi
- Commit: `6797353c7cb5409e3d388e9e8f13954f9bb5f609`
- Contract path: `contracts/side-entrance/SideEntranceLenderPool.sol`
- Functions of interest: `deposit`, `flashLoan`, `withdraw`
- Source language: Solidity

Reason for selection:
- canonical flash-loan accounting bug with a direct asset-versus-credit mismatch
- compact enough to encode without callback machinery
- naturally yields both local storage-update tasks and one composed exploit theorem
