import pytest
from brownie_tokens import ERC20
import brownie

@pytest.fixture(scope="module")
def coins(alice):
    contracts = [ERC20() for i in range(3)]
    for c in contracts:
        c._mint_for_testing(alice, 10**18, {'from': alice})
    return contracts


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
    lp_token.setMinter(contract, {"from": alice})
    for coin in coins:
        coin.approve(contract, 2**256-1, {'from': alice})
    contract.add_liquidity([10**18, 10**18, 10**18], 0, {'from': alice})
    yield contract


@pytest.fixture(scope="module")
def lp_token(RewardsToken, alice, lp_staker, eps_staker):
    contract = RewardsToken.deploy("LP Token", "LP", lp_staker, {'from': alice})
    lp_staker.addPool(contract, 0, {'from': alice})
    yield contract


@pytest.fixture(scope="module")
def token2(bob, swap, lp_token):
    contract = ERC20()
    contract._mint_for_testing(bob, 1000000 * 10**18)
    contract.approve(lp_token, 2**256-1, {'from': bob})
    return contract



def test_reward(lp_token, token2, alice, bob, charlie, lp_staker, chain):
    lp_token.addReward(token2, bob, 86400 * 7, {'from': alice})
    lp_token.transfer(bob, 10**18, {'from': alice})
    lp_token.approve(charlie, 10**18, {'from': alice})
    lp_token.transferFrom(alice, charlie, 10**18, {'from': charlie})

    lp_token.approve(lp_staker, 10**18, {'from': bob})
    lp_token.approve(lp_staker, 10**18, {'from': charlie})
    lp_staker.deposit(2, 10**18, {'from': bob})
    lp_staker.deposit(2, 10**18 // 2, {'from': charlie})

    amount = token2.totalSupply()
    lp_token.notifyRewardAmount(token2, amount, {'from': bob})
    assert token2.balanceOf(bob) == 0
    assert token2.balanceOf(lp_token) == amount

    chain.sleep(86400 * 10)
    chain.mine()
    lp_token.getReward({'from': alice})
    lp_token.getReward({'from': bob})
    lp_token.getReward({'from': charlie})

    balances = [token2.balanceOf(i) for i in (alice, bob, charlie)]
    assert balances[0] > 0
    assert balances[0] == balances[1] == balances[2]
    assert sum(balances) == pytest.approx(amount)


def test_remove_liquidity(lp_token, swap, token2, alice, bob, charlie, chain):
    lp_token.addReward(token2, bob, 86400 * 7, {'from': alice})
    lp_token.transfer(bob, 10**18, {'from': alice})
    lp_token.transfer(charlie, 10**18, {'from': alice})

    amount = token2.totalSupply()
    lp_token.notifyRewardAmount(token2, amount, {'from': bob})

    chain.sleep(86400)
    chain.mine()

    lp_token.getReward({'from': alice})
    lp_token.getReward({'from': bob})
    lp_token.getReward({'from': charlie})

    balances = [token2.balanceOf(i) for i in (alice, bob, charlie)]
    assert sum(balances) == pytest.approx(amount // 7, rel=1e-4)

    swap.remove_liquidity(10**18, [0, 0, 0], {'from': charlie})

    chain.sleep(86400)
    chain.mine()

    lp_token.getReward({'from': alice})
    lp_token.getReward({'from': bob})
    lp_token.getReward({'from': charlie})

    new_balances = [token2.balanceOf(i) for i in (alice, bob, charlie)]
    assert new_balances[2] == balances[2]
    assert sum(new_balances) == pytest.approx(amount // 7 * 2, rel=1e-4)


def test_deposited_balance(lp_token, lp_staker, alice, bob, swap, token2):
    lp_token.addReward(token2, bob, 86400 * 7, {'from': alice})
    amount = token2.totalSupply()
    lp_token.notifyRewardAmount(token2, amount, {'from': bob})

    lp_token.transfer(bob, 3 * 10**18, {'from': alice})
    lp_token.approve(lp_staker, 2**256-1, {'from': bob})

    lp_staker.deposit(2, 10**18, {'from': bob})
    assert lp_token.balanceOf(bob) == 2 * 10**18
    assert lp_token.depositedBalanceOf(bob) == 10**18

    lp_staker.deposit(2, 10**18, {'from': bob})
    assert lp_token.balanceOf(bob) == 10**18
    assert lp_token.depositedBalanceOf(bob) == 2 * 10**18

    with brownie.reverts():
        swap.remove_liquidity(2 * 10**18, [0, 0, 0], {'from': bob})
    swap.remove_liquidity(10**18, [0, 0, 0], {'from': bob})

    assert lp_token.balanceOf(bob) == 0
    assert lp_token.depositedBalanceOf(bob) == 2 * 10**18
    assert lp_token.totalSupply() == 2*10**18

    lp_staker.withdraw(2, 10**18, {'from': bob})

    assert lp_token.balanceOf(bob) == 10**18
    assert lp_token.depositedBalanceOf(bob) == 10**18

    lp_staker.withdraw(2, 10**18, {'from': bob})
    assert lp_token.balanceOf(bob) == 2 * 10**18
    assert lp_token.depositedBalanceOf(bob) == 0

    swap.remove_liquidity(10**18, [0, 0, 0], {'from': bob})
    assert lp_token.balanceOf(bob) == 10**18
    assert lp_token.depositedBalanceOf(bob) == 0
    assert lp_token.totalSupply() == 10**18

    swap.remove_liquidity(10**18, [0, 0, 0], {'from': bob})
    assert lp_token.balanceOf(bob) == 0
    assert lp_token.depositedBalanceOf(bob) == 0
    assert lp_token.totalSupply() == 0
