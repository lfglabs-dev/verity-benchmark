import Benchmark.Cases.Lido.VaulthubLocked.Specs
import Verity.Proofs.Stdlib.Automation
import Mathlib.Tactic.Set

namespace Benchmark.Cases.Lido.VaulthubLocked

open Verity
open Verity.EVM.Uint256

/-
  Reference proofs for the Lido VaultHub _locked() solvency properties.
-/

private theorem val_lt_modulus (a : Uint256) : a.val < modulus := a.isLt

-- ceil(a.val / b.val) ≤ a.val when b.val ≥ 1 (and hence < modulus when a : Uint256)
private theorem ceilDiv_nat_le (av bv : Nat) (hb : bv ≥ 1) :
    (av + bv - 1) / bv ≤ av := by
  rcases Nat.eq_or_lt_of_le (Nat.zero_le av) with haz | haPos
  · -- av = 0
    subst haz
    show (0 + bv - 1) / bv ≤ 0
    simp only [Nat.zero_add]
    exact Nat.le_of_eq (Nat.div_eq_of_lt (by omega : bv - 1 < bv))
  · -- av ≥ 1, so av - 1 ≥ 0
    have hRw : av + bv - 1 = (av - 1) + bv := by omega
    rw [hRw, Nat.add_div_right _ (by omega : bv > 0)]
    have := Nat.div_le_self (av - 1) bv
    omega

private theorem ceilDiv_nat_lt_modulus' (a b : Uint256) (hb : b.val ≥ 1) :
    (a.val + b.val - 1) / b.val < modulus := by
  have := ceilDiv_nat_le a.val b.val hb
  have := val_lt_modulus a
  omega

/-! ## Helper: ceilDiv at the Nat level -/

private theorem ceilDiv_val (a b : Uint256) (hb : b > 0) :
    (ceilDiv a b).val = (a.val + b.val - 1) / b.val % modulus := by
  simp [ceilDiv]
  have hbne : b ≠ 0 := by
    intro h; rw [h] at hb; simp [Verity.Core.Uint256.lt_def] at hb
  simp [hbne]

theorem ceildiv_sandwich
    (x d : Uint256)
    (hd : d > 0)
    (hNoOverflow : (ceilDiv x d).val * d.val < modulus) :
    ceildiv_sandwich_spec x d := by
  unfold ceildiv_sandwich_spec
  intro _ _
  simp [Verity.Core.Uint256.le_def]
  have hMulEq : (mul (ceilDiv x d) d).val = (ceilDiv x d).val * d.val := by
    simp [HMul.hMul, Verity.Core.Uint256.mul, Verity.Core.Uint256.ofNat]
    exact Nat.mod_eq_of_lt hNoOverflow
  rw [hMulEq]
  have hdPos : 0 < d.val := by
    simp [Verity.Core.Uint256.lt_def] at hd; exact hd
  have hCeilVal := ceilDiv_val x d hd
  rw [hCeilVal]
  have hqLt := ceilDiv_nat_lt_modulus' x d hdPos
  rw [Nat.mod_eq_of_lt hqLt]
  -- Standard ceiling property: ceil(n/d) * d ≥ n
  -- Assign concrete variables so omega can work
  let q := (x.val + d.val - 1) / d.val
  let r := (x.val + d.val - 1) % d.val
  have hEuclid : d.val * q + r = x.val + d.val - 1 := Nat.div_add_mod ..
  have hRem : r < d.val := Nat.mod_lt _ hdPos
  -- Goal: x.val ≤ q * d.val
  -- From hEuclid: q * d.val = x.val + d.val - 1 - r ≥ x.val (since d.val - 1 ≥ r is not guaranteed,
  -- but d.val - 1 - r ≥ -(d.val - 1) and we add x.val + d.val - 1 - r.
  -- Actually: q * d.val = x + d - 1 - r. Since r ≤ d - 1 (from hRem), q * d ≥ x + d - 1 - (d - 1) = x.
  show x.val ≤ q * d.val
  have hComm : q * d.val = d.val * q := Nat.mul_comm q d.val
  omega

-- Helper: ceilDiv for raw Nat values (used in shares_conversion_monotone)
private theorem ceilDiv_raw_lt_modulus (n : Nat) (ts : Uint256) (hts : ts.val ≥ 1) (hn : n < modulus) :
    (n + ts.val - 1) / ts.val < modulus := by
  have := ceilDiv_nat_le n ts.val hts
  omega

theorem shares_conversion_monotone
    (a b : Uint256)
    (totalPooledEther totalShares : Uint256)
    (hTS : totalShares > 0)
    (hNoOverflow : a.val * totalPooledEther.val < modulus) :
    shares_conversion_monotone_spec a b totalPooledEther totalShares := by
  unfold shares_conversion_monotone_spec
  intro hab hNoOv
  unfold getPooledEthBySharesRoundUp
  simp [Verity.Core.Uint256.le_def]
  have hTSPos : totalShares.val > 0 := by
    simp [Verity.Core.Uint256.lt_def] at hTS; exact hTS
  have habVal : b.val ≤ a.val := by
    simp [Verity.Core.Uint256.le_def] at hab; exact hab
  have hBNoOverflow : b.val * totalPooledEther.val < modulus :=
    Nat.lt_of_le_of_lt (Nat.mul_le_mul_right _ habVal) hNoOverflow
  have hMulA : (mul a totalPooledEther).val = a.val * totalPooledEther.val := by
    simp [HMul.hMul, Verity.Core.Uint256.mul, Verity.Core.Uint256.ofNat]
    exact Nat.mod_eq_of_lt hNoOverflow
  have hMulB : (mul b totalPooledEther).val = b.val * totalPooledEther.val := by
    simp [HMul.hMul, Verity.Core.Uint256.mul, Verity.Core.Uint256.ofNat]
    exact Nat.mod_eq_of_lt hBNoOverflow
  have hCeilA := ceilDiv_val (mul a totalPooledEther) totalShares hTS
  have hCeilB := ceilDiv_val (mul b totalPooledEther) totalShares hTS
  rw [hCeilA, hCeilB, hMulA, hMulB]
  have hqaLt := ceilDiv_raw_lt_modulus (a.val * totalPooledEther.val) totalShares hTSPos hNoOverflow
  have hqbLt := ceilDiv_raw_lt_modulus (b.val * totalPooledEther.val) totalShares hTSPos hBNoOverflow
  rw [Nat.mod_eq_of_lt hqaLt, Nat.mod_eq_of_lt hqbLt]
  exact Nat.div_le_div_right (by
    have : b.val * totalPooledEther.val ≤ a.val * totalPooledEther.val :=
      Nat.mul_le_mul_right _ habVal
    omega)

theorem max_liability_shares_bound
    (maxLiabilityShares liabilityShares : Uint256)
    (hBound : maxLiabilityShares ≥ liabilityShares) :
    max_liability_shares_bound_spec maxLiabilityShares liabilityShares := by
  unfold max_liability_shares_bound_spec
  exact hBound

theorem reserve_ratio_bounds
    (reserveRatioBP : Uint256)
    (hPos : reserveRatioBP > 0)
    (hLt : reserveRatioBP < TOTAL_BASIS_POINTS) :
    reserve_ratio_bounds_spec reserveRatioBP := by
  unfold reserve_ratio_bounds_spec
  exact ⟨hPos, hLt⟩

-- Helper for locked_funds_solvency: ceilDiv of product < modulus
private theorem ceilDiv_prod_lt_modulus (prod : Nat) (comp : Uint256) (hcomp : comp.val ≥ 1) (hprod : prod < modulus) :
    (prod + comp.val - 1) / comp.val < modulus := by
  have := ceilDiv_nat_le prod comp.val hcomp
  omega

theorem locked_funds_solvency
    (maxLiabilityShares liabilityShares : Uint256)
    (minimalReserve reserveRatioBP : Uint256)
    (totalPooledEther totalShares : Uint256)
    (hMaxLS : maxLiabilityShares ≥ liabilityShares)
    (hRR_pos : reserveRatioBP > 0)
    (hRR_lt : reserveRatioBP < TOTAL_BASIS_POINTS)
    (hTS : totalShares > 0)
    (_hTPE : totalPooledEther > 0)
    (hNoOverflow1 : maxLiabilityShares.val * totalPooledEther.val < modulus)
    (hNoOverflow2 : (getPooledEthBySharesRoundUp maxLiabilityShares totalPooledEther totalShares).val
                    * reserveRatioBP.val < modulus)
    (hNoOverflow3 : let liab := getPooledEthBySharesRoundUp maxLiabilityShares totalPooledEther totalShares
                    let reserve := ceilDiv (mul liab reserveRatioBP) (sub TOTAL_BASIS_POINTS reserveRatioBP)
                    let eff := if reserve ≥ minimalReserve then reserve else minimalReserve
                    liab.val + eff.val < modulus)
    (hNoOverflow4 : (locked maxLiabilityShares minimalReserve reserveRatioBP totalPooledEther totalShares).val
                    * (sub TOTAL_BASIS_POINTS reserveRatioBP).val < modulus)
    (hNoOverflow5 : (getPooledEthBySharesRoundUp liabilityShares totalPooledEther totalShares).val
                    * TOTAL_BASIS_POINTS.val < modulus) :
    locked_funds_solvency_spec maxLiabilityShares liabilityShares minimalReserve reserveRatioBP
      totalPooledEther totalShares := by
  unfold locked_funds_solvency_spec
  simp [Verity.Core.Uint256.le_def]
  set liabilityMax := getPooledEthBySharesRoundUp maxLiabilityShares totalPooledEther totalShares
  set liabilityLS := getPooledEthBySharesRoundUp liabilityShares totalPooledEther totalShares
  set complement := sub TOTAL_BASIS_POINTS reserveRatioBP
  set lockedVal := locked maxLiabilityShares minimalReserve reserveRatioBP totalPooledEther totalShares

  have hLHSEq : (mul lockedVal complement).val = lockedVal.val * complement.val := by
    simp [HMul.hMul, Verity.Core.Uint256.mul, Verity.Core.Uint256.ofNat]
    exact Nat.mod_eq_of_lt hNoOverflow4
  have hRHSEq : (mul liabilityLS TOTAL_BASIS_POINTS).val = liabilityLS.val * TOTAL_BASIS_POINTS.val := by
    simp [HMul.hMul, Verity.Core.Uint256.mul, Verity.Core.Uint256.ofNat]
    exact Nat.mod_eq_of_lt hNoOverflow5
  rw [hLHSEq, hRHSEq]

  have hMonotone : liabilityMax.val ≥ liabilityLS.val := by
    have hmono := shares_conversion_monotone maxLiabilityShares liabilityShares
      totalPooledEther totalShares hTS hNoOverflow1
    unfold shares_conversion_monotone_spec at hmono
    have hM := hmono hMaxLS hNoOverflow1
    simp [Verity.Core.Uint256.le_def] at hM
    exact hM

  suffices h : lockedVal.val * complement.val ≥ liabilityMax.val * TOTAL_BASIS_POINTS.val by
    exact Nat.le_trans (Nat.mul_le_mul_right _ hMonotone) h

  have hRRVal : reserveRatioBP.val > 0 := by
    simp [Verity.Core.Uint256.lt_def] at hRR_pos; exact hRR_pos
  have hRRLtBP : reserveRatioBP.val < TOTAL_BASIS_POINTS.val := by
    simp [Verity.Core.Uint256.lt_def] at hRR_lt; exact hRR_lt

  have hComplementVal : complement.val = TOTAL_BASIS_POINTS.val - reserveRatioBP.val := by
    have hle : reserveRatioBP.val ≤ TOTAL_BASIS_POINTS.val := Nat.le_of_lt hRRLtBP
    simp [complement, HSub.hSub, Verity.Core.Uint256.sub, hle, Verity.Core.Uint256.ofNat]
    have : TOTAL_BASIS_POINTS.val - reserveRatioBP.val < modulus := by
      have := val_lt_modulus TOTAL_BASIS_POINTS; omega
    exact Nat.mod_eq_of_lt this

  have hCompPos : complement.val > 0 := by rw [hComplementVal]; omega
  have hBPEq : TOTAL_BASIS_POINTS.val = complement.val + reserveRatioBP.val := by
    rw [hComplementVal]; omega

  set reserve := ceilDiv (mul liabilityMax reserveRatioBP) complement
  set effectiveReserve := if reserve ≥ minimalReserve then reserve else minimalReserve

  have hMulLiabRR : (mul liabilityMax reserveRatioBP).val = liabilityMax.val * reserveRatioBP.val := by
    simp [HMul.hMul, Verity.Core.Uint256.mul, Verity.Core.Uint256.ofNat]
    exact Nat.mod_eq_of_lt hNoOverflow2

  have hCompNe : complement ≠ 0 := by
    intro h
    have hv : complement.val = 0 := by rw [h]; rfl
    omega

  have hReserveVal : reserve.val = ((liabilityMax.val * reserveRatioBP.val + complement.val - 1) / complement.val) % modulus := by
    simp only [reserve, ceilDiv, hCompNe, ↓reduceIte, hMulLiabRR]

  have hqLt := ceilDiv_prod_lt_modulus (liabilityMax.val * reserveRatioBP.val) complement hCompPos hNoOverflow2

  have hReserveEq : reserve.val = (liabilityMax.val * reserveRatioBP.val + complement.val - 1) / complement.val := by
    rw [hReserveVal, Nat.mod_eq_of_lt hqLt]

  have hReserveProp : reserve.val * complement.val ≥ liabilityMax.val * reserveRatioBP.val := by
    rw [hReserveEq]
    let n := liabilityMax.val * reserveRatioBP.val + complement.val - 1
    let q := n / complement.val
    let r := n % complement.val
    show liabilityMax.val * reserveRatioBP.val ≤ q * complement.val
    have hEuclid : complement.val * q + r = n := Nat.div_add_mod ..
    have hRem : r < complement.val := Nat.mod_lt _ hCompPos
    have hComm : q * complement.val = complement.val * q := Nat.mul_comm q complement.val
    omega

  have hEffGe : effectiveReserve.val ≥ reserve.val := by
    simp only [effectiveReserve]
    by_cases h : reserve ≥ minimalReserve
    · simp [h]
    · simp [h]
      simp [Verity.Core.Uint256.le_def] at h ⊢
      omega

  have hEffProp : effectiveReserve.val * complement.val ≥ liabilityMax.val * reserveRatioBP.val :=
    Nat.le_trans hReserveProp (Nat.mul_le_mul_right _ hEffGe)

  have hNoAddOverflow : liabilityMax.val + effectiveReserve.val < modulus := hNoOverflow3

  have hLockedEq : lockedVal.val = liabilityMax.val + effectiveReserve.val := by
    change (locked maxLiabilityShares minimalReserve reserveRatioBP totalPooledEther totalShares).val
      = liabilityMax.val + effectiveReserve.val
    simp only [locked, getPooledEthBySharesRoundUp]
    simp only [HAdd.hAdd, Verity.Core.Uint256.add, Verity.Core.Uint256.ofNat]
    exact Nat.mod_eq_of_lt hNoAddOverflow

  rw [hLockedEq, hBPEq, Nat.mul_add, Nat.add_mul]
  exact Nat.add_le_add_left hEffProp _

end Benchmark.Cases.Lido.VaulthubLocked
