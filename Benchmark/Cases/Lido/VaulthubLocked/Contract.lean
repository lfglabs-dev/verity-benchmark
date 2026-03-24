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

  Upstream: lidofinance/core (feat/vaults branch)
  File: contracts/0.8.25/vaults/VaultHub.sol
-/

/-- Total basis points constant (10000) -/
def TOTAL_BASIS_POINTS : Uint256 := 10000

/-- ceil(a / b) for natural numbers, matching Solidity's Math256.ceilDiv -/
noncomputable def ceilDiv (a b : Uint256) : Uint256 :=
  if b = 0 then 0
  else ⟨(a.val + b.val - 1) / b.val % modulus⟩

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
  The core _locked function from VaultHub.sol.
  Given liability shares, a minimal reserve, and a reserve ratio in basis points,
  returns the amount of ether that must be locked on the vault.

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

end Benchmark.Cases.Lido.VaulthubLocked
