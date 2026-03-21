import Benchmark.Cases.UniswapV2.PairFeeAdjustedSwap.Specs

namespace Benchmark.Cases.UniswapV2.PairFeeAdjustedSwap

open Verity
open Verity.EVM.Uint256

/--
Executing `applySwap` makes the stored reserve product match the post-swap balances.
-/
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
  exact ?_

end Benchmark.Cases.UniswapV2.PairFeeAdjustedSwap
