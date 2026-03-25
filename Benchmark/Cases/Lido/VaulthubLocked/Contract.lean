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

/--
  Overflow-safe ceiling division, matching Solidity's Math256.ceilDiv / OpenZeppelin:
    a == 0 ? 0 : (a - 1) / b + 1
  Uses EVM-level sub/div/add rather than Nat-level arithmetic.
-/
def ceilDiv (a b : Uint256) : Uint256 :=
  if a = 0 then 0
  else add (div (sub a 1) b) 1

/--
  Share-to-ether conversion matching Lido's getPooledEthBySharesRoundUp:
    Math256.ceilDiv(shares * totalPooledEther, totalShares)
  We treat totalPooledEther and totalShares as parameters.
-/
def getPooledEthBySharesRoundUp
    (shares : Uint256) (totalPooledEther totalShares : Uint256) : Uint256 :=
  ceilDiv (mul shares totalPooledEther) totalShares

/--
  Pure arithmetic core of the _locked function from VaultHub.sol (3-param overload).
  Given liability shares, a minimal reserve, a reserve ratio in basis points,
  and the Lido protocol state, returns the amount of ether that must be locked.

  Solidity source (VaultHub.sol:1283-1295):
    uint256 liability = _getPooledEthBySharesRoundUp(_liabilityShares);
    uint256 reserve = Math256.ceilDiv(liability * _reserveRatioBP, TOTAL_BASIS_POINTS - _reserveRatioBP);
    return liability + Math256.max(reserve, _minimalReserve);
-/
def locked
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

  -- The _locked function uses ceilDiv which is defined as a pure def above.
  -- Proofs reference the pure `locked` directly.

end Benchmark.Cases.Lido.VaulthubLocked
