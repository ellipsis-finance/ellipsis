
import pytest
from brownie_tokens import ERC20
from brownie import chain


def test_deposit_withdraw(lp_staker, token, alice):
    initial_balance = token.balanceOf(alice)
    deposit = 10000 * 10**18

    lp_staker.deposit(1, deposit, {'from': alice})

    assert token.balanceOf(alice) == initial_balance - deposit

    lp_staker.withdraw(1, deposit // 2, {'from': alice})
    assert token.balanceOf(alice) == initial_balance - deposit // 2


def test_claimable(eps_staker, lp_staker, alice):
    chain.sleep(1001)
    chain.mine()
    deposit = 10000 * 10**18
    tx = lp_staker.deposit(1, deposit, {'from': alice})

    chain.sleep(100)
    chain.mine()
    claimable = lp_staker.claimableReward(1, alice)
    assert claimable == (10000000000000 * (chain[-1].timestamp - tx.timestamp)) * 0.8

    chain.sleep(100)
    chain.mine()
    assert lp_staker.claimableReward(1, alice) == (10000000000000 * (chain[-1].timestamp - tx.timestamp)) * 0.8


def test_claim(eps_staker, lp_staker, alice):
    chain.sleep(1001)
    chain.mine()
    deposit = 10000 * 10**18
    lp_staker.deposit(1, deposit, {'from': alice})

    chain.sleep(100)
    chain.mine()

    claimable = lp_staker.claimableReward(1, alice)
    lp_staker.claim([1], {'from': alice})

    assert lp_staker.claimableReward(1, alice) == 0
    assert eps_staker.earnedBalances(alice)['total'] == claimable

    chain.sleep(100)
    chain.mine()
    lp_staker.claim([1], {'from': alice})

    assert lp_staker.claimableReward(1, alice) == 0
    assert abs(eps_staker.earnedBalances(alice)['total'] - claimable * 2) < 1e18


def test_initial_reward_rate_zero(eps_staker, lp_staker, alice):
    deposit = 10000 * 10**18
    lp_staker.deposit(1, deposit, {'from': alice})

    chain.sleep(100)
    chain.mine()

    assert lp_staker.claimableReward(1, alice) == 0
    lp_staker.claim([1], {'from': alice})
    assert eps_staker.earnedBalances(alice)['total'] == 0

    chain.sleep(1000)
    chain.mine()

    assert lp_staker.claimableReward(1, alice) == 0
    tx = lp_staker.claim([1], {'from': alice})
    assert eps_staker.earnedBalances(alice)['total'] == 0

    chain.sleep(100)
    chain.mine()
    assert lp_staker.claimableReward(1, alice) == (10000000000000 * (chain[-1].timestamp - tx.timestamp)) * 0.8


def test_reward_rate_reduces(lp_staker, alice):
    chain.sleep(1001)
    chain.mine()
    deposit = 10000 * 10**18
    lp_staker.deposit(1, deposit, {'from': alice})

    assert lp_staker.rewardsPerSecond() == 10000000000000
    chain.sleep(1001)
    chain.mine()
    lp_staker.claim([1], {'from': alice})
    assert lp_staker.rewardsPerSecond() == 5000000000000
    chain.sleep(1001)
    chain.mine()
    lp_staker.claim([1], {'from': alice})
    assert lp_staker.rewardsPerSecond() == 0

    lp_staker.withdraw(1, deposit, {'from': alice})


def test_claim_multiple_rewards(lp_staker, alice, bob, token, token2):
    lp_staker.addPool(token2, 0, {'from': alice})
    token2.approve(lp_staker, 2**256-1, {'from': bob})
    deposit = 10000 * 10**18
    chain.sleep(1001)
    chain.mine()
    lp_staker.deposit(1, deposit, {'from': alice})
    lp_staker.deposit(2, deposit//2, {'from': bob})
    chain.sleep(100)
    chain.mine()

    assert lp_staker.claimableReward(1, bob) == 0
    assert lp_staker.claimableReward(2, alice) == 0

    claimable = lp_staker.claimableReward(1, alice)
    assert claimable > 0
    assert claimable == lp_staker.claimableReward(2, bob) * 2


def test_alloc_multiple_pools(eps_staker, lp_staker, alice, token, token2):
    lp_staker.addPool(token2, 0, {'from': alice})
    token2.approve(lp_staker, 2**256-1, {'from': alice})
    deposit = 10000 * 10**18
    chain.sleep(1001)
    chain.mine()

    lp_staker.deposit(1, deposit, {'from': alice})
    lp_staker.deposit(2, deposit * 2, {'from': alice})

    assert lp_staker.totalAllocPoint() == deposit * 3
    assert lp_staker.poolInfo(1)['allocPoint'] == deposit
    assert lp_staker.poolInfo(2)['allocPoint'] == deposit * 2


def test_claim_multiple_pools(eps_staker, lp_staker, alice, token, token2):
    lp_staker.addPool(token2, 0, {'from': alice})
    token2.approve(lp_staker, 2**256-1, {'from': alice})
    deposit = 10000 * 10**18
    chain.sleep(1001)
    chain.mine()

    lp_staker.deposit(1, deposit, {'from': alice})
    deposit_time = lp_staker.deposit(2, deposit//2, {'from': alice}).timestamp

    chain.sleep(100)
    chain.mine()

    claim_time = lp_staker.claim([1], {'from': alice}).timestamp
    period = claim_time - deposit_time
    assert 0.6666 < eps_staker.earnedBalances(alice)['total'] / (period * 10000000000000 * 0.8) <= 2/3

    chain.sleep(100)
    chain.mine()
    claim_time = lp_staker.claim([1, 2], {'from': alice}).timestamp
    period = claim_time - deposit_time
    assert 0.999 < eps_staker.earnedBalances(alice)['total'] / (period * 10000000000000 * 0.8) <= 1


def test_repeated_claims(eps_staker, lp_staker, alice, token):
    deposit = 10000 * 10**18
    chain.sleep(1001)
    chain.mine()
    lp_staker.deposit(1, deposit, {'from': alice})
    chain.sleep(100)
    chain.mine()

    claimable = lp_staker.claimableReward(1, alice)
    lp_staker.claim([1, 1, 1, 1], {'from': alice})
    assert claimable == eps_staker.earnedBalances(alice)['total']


def test_single_emerg_withdraw(lp_staker, alice, bob, token, token2):

    deposit = 10000 * 10**18
    chain.sleep(1001)
    chain.mine()
    lp_staker.deposit(1, deposit, {'from': alice})
    lp_staker.deposit(1, deposit, {'from': bob})
    chain.sleep(10000)
    chain.mine()

    claimable = lp_staker.claimableReward(1, alice)
    lp_staker.emergencyWithdraw(1, {'from': bob})
    assert lp_staker.claimableReward(1, alice) == claimable * 2


def test_multi_emerg_withdraw(lp_staker, alice, bob, token, token2):
    lp_staker.addPool(token2, 0, {'from': alice})
    token2.approve(lp_staker, 2**256-1, {'from': alice})
    token2.approve(lp_staker, 2**256-1, {'from': bob})

    deposit = 10000 * 10**18
    chain.sleep(1001)
    chain.mine()
    lp_staker.deposit(1, deposit, {'from': alice})
    lp_staker.deposit(1, deposit * 2, {'from': bob})
    lp_staker.deposit(2, deposit * 3, {'from': bob})
    lp_staker.deposit(2, deposit * 4, {'from': bob})
    lp_staker.deposit(1, deposit * 5, {'from': alice})
    lp_staker.deposit(1, deposit * 6, {'from': bob})
    lp_staker.deposit(2, deposit * 7, {'from': bob})
    lp_staker.deposit(2, deposit * 8, {'from': bob})
    chain.sleep(100)
    chain.mine()

    lp_staker.emergencyWithdraw(1, {'from': alice})
    lp_staker.emergencyWithdraw(2, {'from': alice})
    lp_staker.emergencyWithdraw(1, {'from': bob})
    lp_staker.emergencyWithdraw(2, {'from': bob})

    assert token.balanceOf(alice) == 1000000 * 10**18
    assert token.balanceOf(bob) == 1000000 * 10**18
    assert token2.balanceOf(alice) == 1000000 * 10**18
    assert token2.balanceOf(bob) == 1000000 * 10**18


def test_pool2(lp_staker, pool2token, alice, bob, token):
    chain.sleep(1001)
    chain.mine()
    deposit = 10000*10**18
    lp_staker.deposit(0, deposit / 10, {'from': alice})
    lp_staker.deposit(1, deposit, {'from': alice})
    chain.sleep(100)
    chain.mine()

    assert lp_staker.claimableReward(0, alice) * 4 == lp_staker.claimableReward(1, alice)
    lp_staker.withdraw(0, deposit / 20, {'from': alice})
    lp_staker.emergencyWithdraw(0, {'from': alice})


def test_oracle(eps_staker, lp_staker, alice, bob, token, token2, oracle):
    oracle.setAnswer(1200000000, {'from': alice})
    lp_staker.addOracle(oracle, {'from': alice})
    lp_staker.addPool(token2, 1, {'from': alice})
    token2.approve(lp_staker, 2**256-1, {'from': bob})
    deposit = 10000 * 10**18
    chain.sleep(1001)
    chain.mine()
    lp_staker.deposit(1, deposit, {'from': alice})
    lp_staker.deposit(2, deposit//2, {'from': bob})
    chain.sleep(500)
    chain.mine()

    assert lp_staker.claimableReward(1, bob) == 0
    assert lp_staker.claimableReward(2, alice) == 0

    claimable = lp_staker.claimableReward(1, alice)
    assert claimable > 0
    assert claimable / (lp_staker.claimableReward(2, bob) / 6) == pytest.approx(1, rel=1e-4)
