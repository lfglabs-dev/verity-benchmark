import Contracts.Common

namespace Benchmark.Cases.Ethereum.DepositContractMinimal

open Verity hiding pure bind
open Verity.EVM.Uint256
open Verity.Stdlib.Math

/-
  Minimal Verity slice of the Ethereum deposit contract deposit path.
  The benchmark keeps the counter logic and chain-start threshold behavior, while
  abstracting away SSZ hashing, Merkle tree maintenance, logs, and calldata length checks.
-/
verity_contract DepositContractMinimal where
  storage
    depositCount : Uint256 := slot 0
    fullDepositCount : Uint256 := slot 1
    chainStarted : Uint256 := slot 2

  function deposit (depositAmount : Uint256) : Unit := do
    let currentDepositCount ← getStorage depositCount
    require (currentDepositCount < 4294967295) "MaxDepositCount"
    require (depositAmount >= 1000000000) "DepositTooSmall"

    setStorage depositCount (add currentDepositCount 1)

    if depositAmount >= 32000000000 then
      let currentFullCount ← getStorage fullDepositCount
      let nextFullCount := add currentFullCount 1
      setStorage fullDepositCount nextFullCount
      if nextFullCount == 65536 then
        setStorage chainStarted 1
      else
        pure ()
    else
      pure ()

  function hasChainStarted () : Bool := do
    let started ← getStorage chainStarted
    return started != 0

end Benchmark.Cases.Ethereum.DepositContractMinimal
