# side_entrance

Source:
- `OpenZeppelin/damn-vulnerable-defi`
- file `contracts/side-entrance/SideEntranceLenderPool.sol`

Focus:
- `deposit`
- `flashLoan`
- `withdraw`
- flash-loan repayment through `deposit`
- pool-balance versus withdrawable-credit coherence

Research notes:
- Side Entrance: https://github.com/OpenZeppelin/damn-vulnerable-defi/blob/6797353c7cb5409e3d388e9e8f13954f9bb5f609/contracts/side-entrance/SideEntranceLenderPool.sol
  Best fit because the core bug is a crisp cross-function accounting failure: the borrower can satisfy `flashLoan` repayment by calling `deposit`, leaving pool ETH restored but also minting withdrawable credit. That maps cleanly to a two-slot Verity state and a composed exploit theorem.
- Truster: https://github.com/OpenZeppelin/damn-vulnerable-defi/blob/master/contracts/truster/TrusterLenderPool.sol
  High value, but the bug is arbitrary external call authority during the loan. Modeling calldata-driven token approval would require materially more surface area than this benchmark.
- The Rewarder: https://github.com/OpenZeppelin/damn-vulnerable-defi/blob/master/contracts/the-rewarder/TheRewarderPool.sol
  Interesting reward-accounting race, but it needs temporal reward rounds and token side effects, so the proof surface is larger than Side Entrance.
- Selfie: https://github.com/OpenZeppelin/damn-vulnerable-defi/blob/master/contracts/selfie/SelfiePool.sol
  Governance snapshot abuse is valuable, but it depends on snapshot token semantics and delayed governance execution, which is heavier than the targeted flash-loan/deposit coupling slice.
- Naive Receiver: https://github.com/OpenZeppelin/damn-vulnerable-defi/blob/master/contracts/naive-receiver/NaiveReceiverLenderPool.sol
  The fixed-fee griefing pattern is compact, but it is less distinctive than Side Entrance and mostly centers on fee charging rather than a broken asset-liability invariant.

Out of scope:
- full callback and EVM call-stack modeling
- ETH transfer side effects
- multi-user interleavings
- challenge setup and recovery script details
