# Ellipsis Finance

## EpsStaker.sol
Based on Synthetix rewards contract, EpsStaker allows users to claim their vesting EPS with an exit penalty of 50%. It also allows users to stake (`stake()`) EPS with or without a lock. Users may claim their rewards (EPS and fees from `StableSwap.vy`) by calling (`getReward()`).

## FeeConverter.sol
This contract converts all fees collected by `StableSwap` and distributes them. Called by the `withdraw_admin_fees()` method in `StableSwap.vy`

## MerkleDistributor.sol
Sets up weekly distribution to veCRV holders.

## LpTokenStaker.sol
Based on MasterChef, LpTokenStaker allows Ellipsis users to stake (`deposit()`) various tokens to receive EPS rewards. Upon claiming rewards (`claim()`), EPS is moved to `EpsStaker.sol`. Users may withdraw their LP tokens by calling `withdraw()`

## StableSwap.vy
Stableswap.vy is a fork of Curve's Stableswap which is a pool of BUSD, USDC and USDT. Upon depositing in the pool a user will receive a LP token.

## Token.vy
A fork of Curve LP tokens template which represents a user's share into a pool.
