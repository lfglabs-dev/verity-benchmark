import Verity.Specs.Common
import Benchmark.Cases.UniswapV2.PairFeeAdjustedSwap.Contract

namespace Benchmark.Cases.UniswapV2.PairFeeAdjustedSwap

open Verity
open Verity.EVM.Uint256

def applySwap_sets_reserve0_spec
    (balance0 : Uint256) (_s s' : ContractState) : Prop :=
  s'.storage 0 = balance0

def applySwap_sets_reserve1_spec
    (balance1 : Uint256) (_s s' : ContractState) : Prop :=
  s'.storage 1 = balance1

def applySwap_sets_reserve_product_spec
    (balance0 balance1 : Uint256) (_s s' : ContractState) : Prop :=
  mul (s'.storage 0) (s'.storage 1) = mul balance0 balance1

def applySwap_enforces_fee_adjusted_invariant_spec
    (_balance0 _balance1 amount0In amount1In : Uint256) (s s' : ContractState) : Prop :=
  let balance0Adjusted := sub (mul (s'.storage 0) 1000) (mul amount0In 3)
  let balance1Adjusted := sub (mul (s'.storage 1) 1000) (mul amount1In 3)
  mul balance0Adjusted balance1Adjusted >= mul (mul (s.storage 0) (s.storage 1)) 1000000

end Benchmark.Cases.UniswapV2.PairFeeAdjustedSwap
