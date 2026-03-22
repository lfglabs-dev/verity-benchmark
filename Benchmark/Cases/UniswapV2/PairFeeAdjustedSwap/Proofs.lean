import Benchmark.Cases.UniswapV2.PairFeeAdjustedSwap.Specs
import Verity.Proofs.Stdlib.Automation

namespace Benchmark.Cases.UniswapV2.PairFeeAdjustedSwap

open Verity
open Verity.EVM.Uint256

private theorem applySwap_slot_write
    (balance0 balance1 amount0In amount1In : Uint256) (s : ContractState)
    (hInput : amount0In != 0 || amount1In != 0)
    (hFee0 : mul balance0 1000 >= mul amount0In 3)
    (hFee1 : mul balance1 1000 >= mul amount1In 3)
    (hK : mul (sub (mul balance0 1000) (mul amount0In 3))
        (sub (mul balance1 1000) (mul amount1In 3))
        >= mul (mul (s.storage 0) (s.storage 1)) 1000000) :
    let s' := ((PairFeeAdjustedSwap.applySwap balance0 balance1 amount0In amount1In).run s).snd
    s'.storage 0 = balance0 ∧
    s'.storage 1 = balance1 := by
  repeat' constructor
  all_goals
    simp [PairFeeAdjustedSwap.applySwap, hInput, hFee0, hFee1, hK,
      PairFeeAdjustedSwap.reserve0, PairFeeAdjustedSwap.reserve1,
      Verity.require, Verity.bind, Bind.bind, Contract.run, ContractResult.snd,
      getStorage, setStorage]

theorem applySwap_sets_reserve0
    (balance0 balance1 amount0In amount1In : Uint256) (s : ContractState)
    (hInput : amount0In != 0 || amount1In != 0)
    (hFee0 : mul balance0 1000 >= mul amount0In 3)
    (hFee1 : mul balance1 1000 >= mul amount1In 3)
    (hK : mul (sub (mul balance0 1000) (mul amount0In 3))
        (sub (mul balance1 1000) (mul amount1In 3))
        >= mul (mul (s.storage 0) (s.storage 1)) 1000000) :
    let s' := ((PairFeeAdjustedSwap.applySwap balance0 balance1 amount0In amount1In).run s).snd
    applySwap_sets_reserve0_spec balance0 s s' := by
  simpa [applySwap_sets_reserve0_spec] using
    (applySwap_slot_write balance0 balance1 amount0In amount1In s hInput hFee0 hFee1 hK).1

theorem applySwap_sets_reserve1
    (balance0 balance1 amount0In amount1In : Uint256) (s : ContractState)
    (hInput : amount0In != 0 || amount1In != 0)
    (hFee0 : mul balance0 1000 >= mul amount0In 3)
    (hFee1 : mul balance1 1000 >= mul amount1In 3)
    (hK : mul (sub (mul balance0 1000) (mul amount0In 3))
        (sub (mul balance1 1000) (mul amount1In 3))
        >= mul (mul (s.storage 0) (s.storage 1)) 1000000) :
    let s' := ((PairFeeAdjustedSwap.applySwap balance0 balance1 amount0In amount1In).run s).snd
    applySwap_sets_reserve1_spec balance1 s s' := by
  simpa [applySwap_sets_reserve1_spec] using
    (applySwap_slot_write balance0 balance1 amount0In amount1In s hInput hFee0 hFee1 hK).2

theorem applySwap_sets_reserve_product
    (balance0 balance1 amount0In amount1In : Uint256) (s : ContractState)
    (hInput : amount0In != 0 || amount1In != 0)
    (hFee0 : mul balance0 1000 >= mul amount0In 3)
    (hFee1 : mul balance1 1000 >= mul amount1In 3)
    (hK : mul (sub (mul balance0 1000) (mul amount0In 3))
        (sub (mul balance1 1000) (mul amount1In 3))
        >= mul (mul (s.storage 0) (s.storage 1)) 1000000) :
    let s' := ((PairFeeAdjustedSwap.applySwap balance0 balance1 amount0In amount1In).run s).snd
    applySwap_sets_reserve_product_spec balance0 balance1 s s' := by
  rcases applySwap_slot_write balance0 balance1 amount0In amount1In s hInput hFee0 hFee1 hK with
    ⟨hReserve0, hReserve1⟩
  simp [applySwap_sets_reserve_product_spec, hReserve0, hReserve1]

theorem applySwap_enforces_fee_adjusted_invariant
    (balance0 balance1 amount0In amount1In : Uint256) (s : ContractState)
    (hInput : amount0In != 0 || amount1In != 0)
    (hFee0 : mul balance0 1000 >= mul amount0In 3)
    (hFee1 : mul balance1 1000 >= mul amount1In 3)
    (hK : mul (sub (mul balance0 1000) (mul amount0In 3))
        (sub (mul balance1 1000) (mul amount1In 3))
        >= mul (mul (s.storage 0) (s.storage 1)) 1000000) :
    let s' := ((PairFeeAdjustedSwap.applySwap balance0 balance1 amount0In amount1In).run s).snd
    applySwap_enforces_fee_adjusted_invariant_spec balance0 balance1 amount0In amount1In s s' := by
  rcases applySwap_slot_write balance0 balance1 amount0In amount1In s hInput hFee0 hFee1 hK with
    ⟨hReserve0, hReserve1⟩
  simp [applySwap_enforces_fee_adjusted_invariant_spec, hReserve0, hReserve1, hK]

end Benchmark.Cases.UniswapV2.PairFeeAdjustedSwap
