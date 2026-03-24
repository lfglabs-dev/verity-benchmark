import Contracts.Common

namespace Benchmark.Cases.Lido.VaulthubLocked

open Verity hiding pure bind
open Verity.EVM.Uint256
open Verity.Stdlib.Math

/-
  Focused Verity slice of the Lido VaultHub _locked() function.
  The real contract computes how much collateral must be locked on a vault to
  cover its stETH liability plus a reserve ratio buffer.

  This benchmark isolates the pure arithmetic of `_locked` and models
  `getPooledEthBySharesRoundUp` as an axiomatised share-to-ether conversion.
  Oracle, rebalance, and minting machinery are elided.

  Upstream: lidofinance/core (master)
  File: contracts/0.8.25/vaults/VaultHub.sol
-/

/-- Total basis points constant (10000) -/
def TOTAL_BASIS_POINTS : Uint256 := 10000

/-- ceil(a / b) for natural numbers, matching Solidity's Math256.ceilDiv -/
noncomputable def ceilDiv (a b : Uint256) : Uint256 :=
  if b = 0 then 0
  else ⟨(a.val + b.val - 1) / b.val % modulus, Nat.mod_lt _ Verity.Core.Uint256.modulus_pos⟩

/--
  Axiomatised share-to-ether conversion.
  In the real contract: ceil(shares * totalPooledEther / totalShares)
  We treat totalPooledEther and totalShares as implicit parameters
  and model the conversion as a function from shares to ether.
-/
noncomputable def getPooledEthBySharesRoundUp
    (shares : Uint256) (totalPooledEther totalShares : Uint256) : Uint256 :=
  ceilDiv (mul shares totalPooledEther) totalShares

/--
  Pure arithmetic core of the _locked function from VaultHub.sol (3-param overload).
  Given max liability shares, a minimal reserve, a reserve ratio in basis points,
  and the Lido protocol state, returns the amount of ether that must be locked.

  Solidity source:
    uint256 liability = _getPooledEthBySharesRoundUp(_liabilityShares);
    uint256 reserve = Math256.ceilDiv(liability * _reserveRatioBP, TOTAL_BASIS_POINTS - _reserveRatioBP);
    return liability + Math256.max(reserve, _minimalReserve);
-/
noncomputable def locked
    (liabilityShares : Uint256)
    (minimalReserve : Uint256)
    (reserveRatioBP : Uint256)
    (totalPooledEther totalShares : Uint256) : Uint256 :=
  let liability := getPooledEthBySharesRoundUp liabilityShares totalPooledEther totalShares
  let reserve := ceilDiv (mul liability reserveRatioBP) (sub TOTAL_BASIS_POINTS reserveRatioBP)
  let effectiveReserve := if reserve ≥ minimalReserve then reserve else minimalReserve
  add liability effectiveReserve

verity_contract VaultHubLocked where
  storage
    -- VaultRecord fields
    maxLiabilityShares : Uint256 := slot 0
    liabilityShares : Uint256 := slot 1
    minimalReserve : Uint256 := slot 2
    -- VaultConnection field
    reserveRatioBP : Uint256 := slot 3
    -- Lido protocol state (axiomatised external reads)
    totalPooledEther : Uint256 := slot 4
    totalShares : Uint256 := slot 5

  -- The _locked function is modeled as a pure `noncomputable def locked` above.
  -- The verity_contract DSL does not support calling external defs in function bodies,
  -- so we keep the contract block storage-only. Proofs reference the pure `locked` directly.

end Benchmark.Cases.Lido.VaulthubLocked
