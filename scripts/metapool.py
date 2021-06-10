from brownie import (
    accounts,
    LpTokenStaker,
    StableSwap,
    RewardsToken,
    StableSwapMeta,
    StableSwapBTC,
    StableSwapMetaBTC,
)


def usd(coin):
    deployer = accounts.load('deployer')
    base_pool = StableSwap.at('0x160CAed03795365F3A589f10C379FfA7d75d4E76')
    lp_staker = LpTokenStaker.at('0xcce949De564fE60e7f96C85e55177F8B9E4CF61b')
    coins = [coin, "0xaF4dE8E872131AE328Ce21D909C74705d3Aaf452"]

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
        "0xdd6df5ffed7b770355de53a9b60577b795a27b66",  # MetapoolFeeConverter
        {"from": deployer},
    )
    lp_token.setMinter(swap, {'from': deployer})

    # lp_staker.addPool(lp_token, 0, {'from': lp_staker.owner()})


def btc(coin):
    deployer = accounts.load('deployer')
    base_pool = StableSwapBTC.at('0x2477fB288c5b4118315714ad3c7Fd7CC69b00bf9')
    lp_staker = LpTokenStaker.at('0xcce949De564fE60e7f96C85e55177F8B9E4CF61b')
    coins = [coin, "0x2a435Ecb3fcC0E316492Dc1cdd62d0F189be5640"]

    symbol = coin.symbol().lower()
    name = f"Ellipsis.finance {symbol}/btcEPS"
    if symbol.endswith("btc"):
        symbol = symbol[:-3]
    lp_token = RewardsToken.deploy(
        name,
        f"{symbol}btcEPS",
        lp_staker,
        {'from': deployer}
    )

    swap = StableSwapMetaBTC.deploy(
        deployer,
        coins,  # coins,
        lp_token,
        base_pool,
        600,  # A
        4000000,  # fee
        5000000000,  # admin fee
        "0xD7571f3E67b553ecd344a713785399471B627A4F",  # PancakeFeeConverter
        {"from": deployer},
    )
    lp_token.setMinter(swap, {'from': deployer})

    # lp_staker.addPool(lp_token, 1, {'from': lp_staker.owner()})
