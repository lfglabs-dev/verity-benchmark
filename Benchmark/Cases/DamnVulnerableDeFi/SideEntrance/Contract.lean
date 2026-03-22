import Contracts.Common

namespace Benchmark.Cases.DamnVulnerableDeFi.SideEntrance

open Verity hiding pure bind
open Verity.EVM.Uint256

/-
  Focused Verity slice of the Damn Vulnerable DeFi Side Entrance pool.
  The model keeps only pool ETH, aggregate credited liabilities, and each
  account's credited balance. The flash-loan callback is compressed into one
  atomic step that repays through `deposit`, restoring pool ETH while still
  minting withdrawable credit for the borrower.
-/
verity_contract SideEntrance where
  storage
    poolBalance : Uint256 := slot 0
    totalCredits : Uint256 := slot 1
    creditOf : Address → Uint256 := slot 2

  function deposit (amount : Uint256) : Unit := do
    let sender ← msgSender
    let oldPoolBalance ← getStorage poolBalance
    let oldTotalCredits ← getStorage totalCredits
    let oldSenderCredit ← getMapping creditOf sender

    setStorage poolBalance (add oldPoolBalance amount)
    setStorage totalCredits (add oldTotalCredits amount)
    setMapping creditOf sender (add oldSenderCredit amount)

  function flashLoanViaDeposit (amount : Uint256) : Unit := do
    let sender ← msgSender
    let oldPoolBalance ← getStorage poolBalance
    let oldTotalCredits ← getStorage totalCredits
    let oldSenderCredit ← getMapping creditOf sender

    require (amount <= oldPoolBalance) "NotEnoughBalance"

    setStorage poolBalance oldPoolBalance
    setStorage totalCredits (add oldTotalCredits amount)
    setMapping creditOf sender (add oldSenderCredit amount)

  function withdraw () : Uint256 := do
    let sender ← msgSender
    let oldPoolBalance ← getStorage poolBalance
    let oldTotalCredits ← getStorage totalCredits
    let senderCredit ← getMapping creditOf sender

    require (senderCredit <= oldPoolBalance) "InsufficientPoolBalance"

    setStorage poolBalance (sub oldPoolBalance senderCredit)
    setStorage totalCredits (sub oldTotalCredits senderCredit)
    setMapping creditOf sender 0

    return senderCredit

end Benchmark.Cases.DamnVulnerableDeFi.SideEntrance
