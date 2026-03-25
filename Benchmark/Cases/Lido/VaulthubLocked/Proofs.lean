import Benchmark.Cases.Lido.VaulthubLocked.Specs
import Verity.Proofs.Stdlib.Automation
import Mathlib.Tactic.Set

namespace Benchmark.Cases.Lido.VaulthubLocked

open Verity
open Verity.EVM.Uint256

/-
  Reference proofs for the Lido VaultHub _locked() solvency properties.
  Adapted for the EVM-faithful ceilDiv: a = 0 ? 0 : (a - 1) / b + 1
-/

private theorem val_lt_modulus (a : Uint256) : a.val < modulus := a.isLt

/-! ## Nat-level helpers for ceiling division -/

-- Nat identity: (a - 1) / b + 1 = (a + b - 1) / b  for a > 0, b > 0
private theorem ceildiv_nat_identity (a b : Nat) (ha : a > 0) (hb : b > 0) :
    (a - 1) / b + 1 = (a + b - 1) / b := by
  have h : a + b - 1 = (a - 1) + b := by omega
  rw [h, Nat.add_div_right _ hb]

-- ceil(a / b) ≤ a when b ≥ 1 (expressed using the (a+b-1)/b form)
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

-- (a - 1) / b + 1 ≤ a when a > 0 and b ≥ 1
private theorem ceilDiv_evm_le (av bv : Nat) (ha : av > 0) (hb : bv ≥ 1) :
    (av - 1) / bv + 1 ≤ av := by
  rw [ceildiv_nat_identity av bv ha (by omega)]
  exact ceilDiv_nat_le av bv hb

-- (a - 1) / b + 1 < modulus when a : Uint256 and b ≥ 1
private theorem ceilDiv_evm_lt_modulus (a b : Uint256) (ha : a.val > 0) (hb : b.val ≥ 1) :
    (a.val - 1) / b.val + 1 < modulus := by
  have := ceilDiv_evm_le a.val b.val ha hb
  have := val_lt_modulus a
  omega

-- (a + b - 1) / b < modulus (old form, used in some helpers)
private theorem ceilDiv_nat_lt_modulus' (a b : Uint256) (hb : b.val ≥ 1) :
    (a.val + b.val - 1) / b.val < modulus := by
  have := ceilDiv_nat_le a.val b.val hb
  have := val_lt_modulus a
  omega

/-! ## Helper: ceilDiv val-level unfolding -/

-- When a.val > 0 and b > 0, (ceilDiv a b).val = (a.val - 1) / b.val + 1
private theorem ceilDiv_val_pos (a b : Uint256) (ha : a.val > 0) (hb : b.val > 0) :
    (ceilDiv a b).val = (a.val - 1) / b.val + 1 := by
  have haNe : a ≠ 0 := by
    intro h; rw [h] at ha; simp [Verity.Core.Uint256.val_zero] at ha
  -- Unfold ceilDiv, eliminate the if-branch
  simp only [ceilDiv, haNe, ↓reduceIte]
  -- Goal: (add (div (sub a 1) b) 1).val = (a.val - 1) / b.val + 1
  -- Step 1: (sub a 1).val = a.val - 1 (since a.val > 0, no underflow)
  have hSubVal : (sub a 1).val = a.val - 1 := by
    have h1le : (1 : Uint256).val ≤ a.val := by
      simp [Verity.Core.Uint256.val_one]; omega
    have := sub_eq_of_le h1le
    simp [Verity.Core.Uint256.val_one] at this
    exact this
  -- Step 2: (div (sub a 1) b).val = (a.val - 1) / b.val
  have hDivVal : (div (sub a 1) b).val = (a.val - 1) / b.val := by
    have hbne : b.val ≠ 0 := by omega
    simp only [HDiv.hDiv, Verity.Core.Uint256.div, hbne, ↓reduceIte, Verity.Core.Uint256.ofNat, hSubVal]
    have hDivLt : (a.val - 1) / b.val < modulus := by
      have := Nat.div_le_self (a.val - 1) b.val
      have := val_lt_modulus a
      omega
    exact Nat.mod_eq_of_lt hDivLt
  -- Step 3: (add (div ...) 1).val = (a.val - 1) / b.val + 1
  have hAddLt : (a.val - 1) / b.val + 1 < modulus :=
    ceilDiv_evm_lt_modulus a b ha (by omega)
  simp only [HAdd.hAdd, Verity.Core.Uint256.add, Verity.Core.Uint256.ofNat, hDivVal,
             Verity.Core.Uint256.val_one]
  exact Nat.mod_eq_of_lt hAddLt

-- When a = 0, (ceilDiv a b).val = 0
private theorem ceilDiv_val_zero (b : Uint256) :
    (ceilDiv 0 b).val = 0 := by
  simp [ceilDiv]

-- Combined: (ceilDiv a b).val matches the (a+b-1)/b form when b > 0
-- This bridges the new EVM-level ceilDiv back to the old Nat-level expression
private theorem ceilDiv_val_eq_nat (a b : Uint256) (hb : b.val > 0) :
    (ceilDiv a b).val = (a.val + b.val - 1) / b.val := by
  by_cases ha : a.val = 0
  · -- a = 0: ceilDiv 0 b = 0, and (0 + b - 1) / b = (b-1)/b = 0
    have haEq : a = 0 := by
      ext; simp [ha, Verity.Core.Uint256.val_zero]
    rw [haEq, ceilDiv_val_zero]
    simp only [Verity.Core.Uint256.val_zero, Nat.zero_add]
    exact (Nat.div_eq_of_lt (by omega)).symm
  · -- a > 0
    have haPos : a.val > 0 := Nat.pos_of_ne_zero ha
    rw [ceilDiv_val_pos a b haPos hb]
    rw [ceildiv_nat_identity a.val b.val haPos hb]

-- Legacy-compatible form with mod (the mod is a no-op since value < modulus)
private theorem ceilDiv_val (a b : Uint256) (hb : b > 0) :
    (ceilDiv a b).val = (a.val + b.val - 1) / b.val % modulus := by
  have hbPos : b.val > 0 := by simp [Verity.Core.Uint256.lt_def] at hb; exact hb
  rw [ceilDiv_val_eq_nat a b hbPos]
  exact (Nat.mod_eq_of_lt (ceilDiv_nat_lt_modulus' a b (by omega))).symm

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
  let q := (x.val + d.val - 1) / d.val
  let r := (x.val + d.val - 1) % d.val
  have hEuclid : d.val * q + r = x.val + d.val - 1 := Nat.div_add_mod ..
  have hRem : r < d.val := Nat.mod_lt _ hdPos
  show x.val ≤ q * d.val
  have hComm : q * d.val = d.val * q := Nat.mul_comm q d.val
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
  -- Use the bridge lemma to get back to the (n + d - 1) / d form
  have hCeilA := ceilDiv_val_eq_nat (mul a totalPooledEther) totalShares hTSPos
  have hCeilB := ceilDiv_val_eq_nat (mul b totalPooledEther) totalShares hTSPos
  rw [hCeilA, hCeilB, hMulA, hMulB]
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

  -- Use the bridge lemma to convert EVM ceilDiv to the Nat-level (n+d-1)/d form
  have hReserveEq : reserve.val = (liabilityMax.val * reserveRatioBP.val + complement.val - 1) / complement.val := by
    simp only [reserve]
    rw [ceilDiv_val_eq_nat (mul liabilityMax reserveRatioBP) complement hCompPos, hMulLiabRR]

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
