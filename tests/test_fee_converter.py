import pytest
from brownie_tokens import ERC20

@pytest.fixture(scope="module")
def lp_token(alice, Token):
    yield Token.deploy("Lp Token", "LP", 0, {'from': alice})


@pytest.fixture(scope="module")
def coins(alice):
    yield [ERC20() for i in range(3)]


@pytest.fixture(scope="module")
def swap(alice, bob, StableSwap, lp_token, fee_converter, coins):
    contract = StableSwap.deploy(
        alice,
        coins,  # coins,
        lp_token,
        1500,  # A
        40000000,  # fee
        5000000000,  # admin fee
        fee_converter,
        {"from": alice},
    )
    lp_token.set_minter(contract, {"from": alice})
    yield contract


def test_fee_conversion(alice, bob, swap, coins, lp_token, fee_converter, eps_staker):
    eps_staker.addReward(coins[0], fee_converter, {'from': alice})
    for coin in coins:
        coin._mint_for_testing(alice, 100000*10**18)
        coin.approve(swap, 2**256-1, {'from': alice})
    swap.add_liquidity([10000*10**18, 10000*10**18, 10000*10**18], 0, {'from': alice})
    swap.exchange(0, 1, 10000*10**18, 0, {'from': alice})
    swap.exchange(1, 2, 10000*10**18, 0, {'from': alice})
    swap.exchange(2, 0, 10000*10**18, 0, {'from': alice})

    swap.withdraw_admin_fees({'from': bob})
