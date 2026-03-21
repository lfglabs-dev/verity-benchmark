import Contracts.Common

namespace Benchmark.Cases.UniswapV2.PairFeeAdjustedSwap

open Verity hiding pure bind
open Verity.EVM.Uint256

/- 
  Focused Verity slice of `UniswapV2Pair.swap`.
  The benchmark starts after transfers and callbacks have already produced observed
  balances and inferred input amounts. It keeps the SafeMath-backed 0.3% fee-adjusted
  product guard and the final reserve writes, while omitting token movement, oracle
  accumulation, and event emission.
-/
verity_contract PairFeeAdjustedSwap where
  storage
    reserve0 : Uint256 := slot 0
    reserve1 : Uint256 := slot 1

  function applySwap
      (balance0 : Uint256, balance1 : Uint256, amount0In : Uint256, amount1In : Uint256) : Unit := do
    let oldReserve0 ← getStorage reserve0
    let oldReserve1 ← getStorage reserve1

    require (amount0In != 0 || amount1In != 0) "InsufficientInputAmount"
    require (mul balance0 1000 >= mul amount0In 3) "InvalidAmount0In"
    require (mul balance1 1000 >= mul amount1In 3) "InvalidAmount1In"

    let balance0Adjusted := sub (mul balance0 1000) (mul amount0In 3)
    let balance1Adjusted := sub (mul balance1 1000) (mul amount1In 3)

    require
      (mul balance0Adjusted balance1Adjusted >= mul (mul oldReserve0 oldReserve1) 1000000)
      "K"

    setStorage reserve0 balance0
    setStorage reserve1 balance1

end Benchmark.Cases.UniswapV2.PairFeeAdjustedSwap
