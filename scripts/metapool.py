from brownie import (
    accounts,
    MultiFeeDistribution,
    LpTokenStaker,
    StableSwap,
    RewardsToken,
    StableSwapMeta,
    MetapoolFeeConverter,
)


def main(coin):
    deployer = accounts.load('deployer')
    base_pool = StableSwap.at('0x160CAed03795365F3A589f10C379FfA7d75d4E76')
    lp_staker = LpTokenStaker.at('0xcce949De564fE60e7f96C85e55177F8B9E4CF61b')
    eps_staker = MultiFeeDistribution.at('0x4076CC26EFeE47825917D0feC3A79d0bB9a6bB5c')
    coins = [coin, "0xaF4dE8E872131AE328Ce21D909C74705d3Aaf452"]

    fee_converter = MetapoolFeeConverter.deploy({"from": deployer})
    fee_converter.setFeeDistributor(eps_staker, {'from': deployer})
    symbol = coin.symbol()
    lp_token = RewardsToken.deploy(
        f"Ellipsis.finance {symbol}/3EPS",
        f"{symbol.lower()}3EPS",
        lp_staker,
        {'from': deployer}
    )

    swap = StableSwapMeta.deploy(
        deployer,
        coins,  # coins,
        lp_token,
        base_pool,
        600,  # A
        4000000,  # fee
        5000000000,  # admin fee
        fee_converter,
        {"from": deployer},
    )
    lp_token.setMinter(swap, {'from': deployer})

    # lp_staker.addPool(lp_token, 0, {'from': lp_staker.owner()})
    # eps_staker.approveRewardDistributor(base_pool.coins(0), fee_converter, True, {'from': eps_staker.owner()})
