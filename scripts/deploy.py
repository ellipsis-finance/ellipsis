from brownie import (
    accounts,
    Contract,
    MultiFeeDistribution,
    LpTokenStaker,
    FeeConverter,
    MerkleDistributor,
    StableSwap,
    Token,
)


DAY = 86400
MONTH = DAY * 30
YEAR = DAY * 365

TOTAL_SUPPLY = 1000000000 * 10 ** 18
REWARD_AMOUNTS = [0.05, 0.04, 0.03, 0.18, 0.125, 0.0625, 0.03125, 0.03125, 0]
REWARD_OFFSETS = [0, MONTH, MONTH * 2, MONTH * 3, YEAR, YEAR * 2, YEAR * 3, YEAR * 4, YEAR * 5]

LAUNCH_OFFSET = 3600


def main():
    deployer = accounts.load('deployer')
    lp_token = Token.deploy("Ellipsis.finance BUSD/USDC/USDT", "3EPS", 0, {"from": deployer})
    fee_converter = FeeConverter.deploy({"from": deployer})
    airdrop_distro = MerkleDistributor.deploy(deployer, "0x7EeAC6CDdbd1D0B8aF061742D41877D7F707289a", {'from': deployer})

    coins = [
        "0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56",  # busd
        "0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d",  # usdc
        "0x55d398326f99059fF775485246999027B3197955"   # usdt
    ]
    swap = StableSwap.deploy(
        deployer,
        coins,  # coins,
        lp_token,
        1500,  # A
        4000000,  # fee
        5000000000,  # admin fee
        fee_converter,
        {"from": deployer},
    )
    lp_token.set_minter(swap, {"from": deployer})

    initial_supply = TOTAL_SUPPLY // 5 + (5000*10**18)
    eps = Token.deploy("Ellipsis", "EPS", initial_supply, {"from": deployer})

    cake = Contract('0x05ff2b0db69458a0750badebc4f9e13add608c7f')
    tx = cake.addLiquidityETH(eps, 5000*10**18, 5000*10**18, 10**18, deployer, 2000000000, {'from': deployer})
    cakelp = tx.events['PairCreated']['pair']

    per_period = [int(i * 100000) * TOTAL_SUPPLY // 100000 for i in REWARD_AMOUNTS]
    durations = [REWARD_OFFSETS[i + 1] - REWARD_OFFSETS[i] for i in range(len(REWARD_OFFSETS) - 1)]
    rewards_per_block = [per_period[i] // durations[i] for i in range(len(durations))] + [0]
    offsets = [i + LAUNCH_OFFSET for i in REWARD_OFFSETS]

    lp_staker = LpTokenStaker.deploy(offsets, rewards_per_block, cakelp, {"from": deployer})
    lp_staker.addPool(lp_token, 0, {'from': deployer})

    eps_staker = MultiFeeDistribution.deploy(eps, [lp_staker, airdrop_distro], {"from": deployer})
    eps_staker.addReward(coins[0], fee_converter, {'from': deployer})

    lp_staker.setMinter(eps_staker, {"from": deployer})
    eps.set_minter(eps_staker, {'from': deployer})
    fee_converter.setFeeDistributor(eps_staker, {"from": deployer})
    airdrop_distro.setMinter(eps_staker, {'from': deployer})
