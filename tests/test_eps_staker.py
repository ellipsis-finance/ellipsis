

import brownie
from brownie import chain


def test_stake(eps, eps_staker, alice):
    initial = eps.balanceOf(alice)
    eps_staker.stake(10000, False, {'from': alice})
    assert eps.balanceOf(alice) == initial - 10000
    assert eps.balanceOf(eps_staker) == 10000

    assert eps_staker.totalBalance(alice) == 10000
    assert eps_staker.unlockedBalance(alice) == 10000
    assert eps_staker.lockedBalances(alice) == [0, 0, 0, []]
    assert eps_staker.earnedBalances(alice) == [0, []]

    assert eps_staker.totalSupply() == 10000
    assert eps_staker.lockedSupply() == 0


def test_stake_multiple(eps, eps_staker, alice, bob):
    initial = eps.balanceOf(alice)
    eps_staker.stake(10000, False, {'from': alice})
    eps_staker.stake(50000, False, {'from': alice})
    eps_staker.stake(6666, False, {'from': bob})
    assert eps.balanceOf(alice) == initial - 60000
    assert eps.balanceOf(eps_staker) == 66666

    assert eps_staker.totalBalance(alice) == 60000
    assert eps_staker.unlockedBalance(alice) == 60000
    assert eps_staker.lockedBalances(alice) == [0, 0, 0, []]
    assert eps_staker.earnedBalances(alice) == [0, []]

    assert eps_staker.totalSupply() == 66666
    assert eps_staker.lockedSupply() == 0


def test_mint_multiple(eps, eps_staker, alice):
    tx = eps_staker.mint(alice, 30000, {'from': alice})
    locked_until = (tx.timestamp // 604800 + 13) * 604800
    chain.sleep(604800)
    chain.mine()

    eps_staker.mint(alice, 50000, {'from': alice})
    eps_staker.mint(alice, 40000, {'from': alice})
    chain.sleep(604800*2)
    chain.mine()

    eps_staker.mint(alice, 20000, {'from': alice})

    assert eps_staker.unlockedBalance(alice) == 0
    assert eps_staker.earnedBalances(alice) == [140000, [[30000, locked_until], [90000, locked_until + 604800], [20000, locked_until + 604800 * 3]]]
    assert eps_staker.totalSupply() == 140000
    assert eps_staker.lockedSupply() == 0
    assert eps_staker.withdrawableBalance(alice) == [70000, 70000]


def test_stake_locked(eps, eps_staker, alice):
    initial = eps.balanceOf(alice)
    tx = eps_staker.stake(10000, True, {'from': alice})
    locked_until = (tx.timestamp // 604800 + 13) * 604800
    assert eps.balanceOf(alice) == initial - 10000
    assert eps.balanceOf(eps_staker) == 10000

    assert eps_staker.totalBalance(alice) == 10000
    assert eps_staker.unlockedBalance(alice) == 0
    assert eps_staker.lockedBalances(alice) == [10000, 0, 10000, [[10000, locked_until]]]
    assert eps_staker.earnedBalances(alice) == [0, []]

    assert eps_staker.totalSupply() == 10000
    assert eps_staker.lockedSupply() == 10000


def test_stake_locked_multiple(eps, eps_staker, alice):
    initial = eps.balanceOf(alice)
    tx = eps_staker.stake(10000, True, {'from': alice})
    locked_until = (tx.timestamp // 604800 + 13) * 604800
    eps_staker.stake(20000, True, {'from': alice})
    chain.sleep(604800)
    eps_staker.stake(30000, True, {'from': alice})
    chain.sleep(604800 * 3)
    eps_staker.stake(40000, True, {'from': alice})

    assert eps.balanceOf(alice) == initial - 100000
    assert eps.balanceOf(eps_staker) == 100000

    assert eps_staker.totalBalance(alice) == 100000
    assert eps_staker.unlockedBalance(alice) == 0
    assert eps_staker.lockedBalances(alice) == [100000, 0, 100000, [[30000, locked_until], [30000, locked_until + 604800], [40000, locked_until + 604800 * 4]]]
    assert eps_staker.earnedBalances(alice) == [0, []]

    assert eps_staker.totalSupply() == 100000
    assert eps_staker.lockedSupply() == 100000


def test_locks_expire(eps, eps_staker, alice):
    initial = eps.balanceOf(alice)
    tx = eps_staker.stake(20000, True, {'from': alice})
    locked_until = (tx.timestamp // 604800 + 13) * 604800
    chain.sleep(604800)
    eps_staker.stake(30000, True, {'from': alice})
    chain.sleep(604800)
    eps_staker.stake(50000, True, {'from': alice})
    chain.mine(timestamp=locked_until+1)

    assert eps.balanceOf(alice) == initial - 100000
    assert eps.balanceOf(eps_staker) == 100000

    assert eps_staker.totalBalance(alice) == 100000
    assert eps_staker.unlockedBalance(alice) == 0
    assert eps_staker.lockedBalances(alice) == [100000, 20000, 80000, [[30000, locked_until + 604800], [50000, locked_until + 604800 * 2]]]
    assert eps_staker.earnedBalances(alice) == [0, []]

    assert eps_staker.totalSupply() == 100000
    assert eps_staker.lockedSupply() == 100000

    chain.sleep(604800)
    chain.mine()
    assert eps_staker.lockedBalances(alice) == [100000, 50000, 50000, [[50000, locked_until + 604800 * 2]]]

    eps_staker.withdrawExpiredLocks({'from': alice})
    assert eps.balanceOf(alice) == initial - 50000
    assert eps.balanceOf(eps_staker) == 50000

    assert eps_staker.totalBalance(alice) == 50000
    assert eps_staker.unlockedBalance(alice) == 0
    assert eps_staker.lockedBalances(alice) == [50000, 0, 50000, [[50000, locked_until + 604800 * 2]]]
    assert eps_staker.earnedBalances(alice) == [0, []]
    assert eps_staker.totalSupply() == 50000
    assert eps_staker.lockedSupply() == 50000

    chain.sleep(604800)
    chain.mine()
    assert eps_staker.lockedBalances(alice) == [50000, 50000, 0, []]
    eps_staker.withdrawExpiredLocks({'from': alice})
    assert eps.balanceOf(alice) == initial
    assert eps.balanceOf(eps_staker) == 0

    assert eps_staker.totalBalance(alice) == 0
    assert eps_staker.unlockedBalance(alice) == 0
    assert eps_staker.lockedBalances(alice) == [0, 0, 0, []]
    assert eps_staker.earnedBalances(alice) == [0, []]
    assert eps_staker.totalSupply() == 0
    assert eps_staker.lockedSupply() == 0


def test_withdraw_unlocked(eps, eps_staker, alice):
    initial = eps.balanceOf(alice)
    eps_staker.stake(10000, False, {'from': alice})
    eps_staker.withdraw(10000, {'from': alice})
    assert eps.balanceOf(alice) == initial


def test_withdraw_unlocked_partial(eps, eps_staker, alice):
    initial = eps.balanceOf(alice)
    eps_staker.stake(10000, False, {'from': alice})
    eps_staker.withdraw(4000, {'from': alice})
    assert eps.balanceOf(alice) == initial - 6000


def test_withdraw_only_unlocked_with_earned_balance(eps, eps_staker, alice):
    initial = eps.balanceOf(alice)
    eps_staker.stake(10000, False, {'from': alice})
    tx = eps_staker.mint(alice, 30000, {'from': alice})
    locked_until = (tx.timestamp // 604800 + 13) * 604800

    assert eps_staker.earnedBalances(alice) == [30000, [[30000, locked_until]]]

    eps_staker.withdraw(10000, {'from': alice})
    assert eps.balanceOf(alice) == initial
    assert eps_staker.earnedBalances(alice) == [30000, [[30000, locked_until]]]


def test_withdraw_unlocked_and_earned_with_penalty(eps, eps_staker, alice):
    initial = eps.balanceOf(alice)
    eps_staker.stake(10000, False, {'from': alice})
    tx = eps_staker.mint(alice, 30000, {'from': alice})
    locked_until = (tx.timestamp // 604800 + 13) * 604800

    assert eps_staker.earnedBalances(alice) == [30000, [[30000, locked_until]]]

    with brownie.reverts("Insufficient balance after penalty"):
        eps_staker.withdraw(25001, {'from': alice})

    eps_staker.withdraw(25000, {'from': alice})
    assert eps.balanceOf(alice) == initial + 15000
    assert eps_staker.earnedBalances(alice) == [0, []]
    assert eps_staker.totalSupply() == 0


def test_withdraw_unlocked_and_earned_partial(eps, eps_staker, alice):
    initial = eps.balanceOf(alice)
    tx = eps_staker.mint(alice, 30000, {'from': alice})
    locked_until = (tx.timestamp // 604800 + 13) * 604800
    chain.sleep(604800)
    chain.mine()
    eps_staker.stake(10000, False, {'from': alice})
    eps_staker.mint(alice, 60000, {'from': alice})

    eps_staker.withdraw(15000, {'from': alice})
    assert eps.balanceOf(alice) == initial + 5000
    assert eps_staker.earnedBalances(alice) == [80000, [[20000, locked_until], [60000, locked_until + 604800]]]

    eps_staker.withdraw(15000, {'from': alice})
    assert eps.balanceOf(alice) == initial + 20000
    assert eps_staker.earnedBalances(alice) == [50000, [[50000, locked_until + 604800]]]


def test_withdraw_earned_without_penalty(eps, eps_staker, alice):
    initial = eps.balanceOf(alice)
    tx = eps_staker.mint(alice, 30000, {'from': alice})
    locked_until = (tx.timestamp // 604800 + 13) * 604800
    chain.sleep(604800)
    chain.mine()
    eps_staker.mint(alice, 60000, {'from': alice})

    chain.mine(timestamp=locked_until+604801)
    assert eps_staker.earnedBalances(alice) == [0, []]
    assert eps_staker.unlockedBalance(alice) == 90000

    with brownie.reverts("Insufficient unlocked balance"):
        eps_staker.withdraw(90001, {'from': alice})

    eps_staker.withdraw(90000, {'from': alice})
    assert eps.balanceOf(alice) == initial + 90000
    assert eps_staker.earnedBalances(alice) == [0, []]
    assert eps_staker.unlockedBalance(alice) == 0
    assert eps_staker.totalSupply() == 0


def test_withdraw_earned_partial_penalty(eps, eps_staker, alice):
    initial = eps.balanceOf(alice)
    tx = eps_staker.mint(alice, 30000, {'from': alice})
    locked_until = (tx.timestamp // 604800 + 13) * 604800
    chain.sleep(604800)
    chain.mine()
    eps_staker.mint(alice, 60000, {'from': alice})

    chain.mine(timestamp=locked_until+1)
    assert eps_staker.earnedBalances(alice) == [60000, [[60000, locked_until + 604800]]]
    assert eps_staker.unlockedBalance(alice) == 30000

    with brownie.reverts("Insufficient balance after penalty"):
        eps_staker.withdraw(60001, {'from': alice})
    eps_staker.withdraw(60000, {'from': alice})
    assert eps.balanceOf(alice) == initial + 60000
    assert eps_staker.earnedBalances(alice) == [0, []]
    assert eps_staker.unlockedBalance(alice) == 0
    assert eps_staker.totalSupply() == 0


def test_exit_penalty(eps, eps_staker, alice):
    initial = eps.balanceOf(alice)
    eps_staker.stake(10000, False, {'from': alice})
    eps_staker.mint(alice, 30000, {'from': alice})
    chain.sleep(604800)
    chain.mine()
    eps_staker.mint(alice, 60000, {'from': alice})

    eps_staker.exit({'from': alice})
    assert eps.balanceOf(alice) == initial + 45000
    assert eps_staker.earnedBalances(alice) == [0, []]
    assert eps_staker.unlockedBalance(alice) == 0
    assert eps_staker.totalSupply() == 0


def test_exit_partial_penalty(eps, eps_staker, alice):
    initial = eps.balanceOf(alice)
    eps_staker.stake(10000, False, {'from': alice})
    tx = eps_staker.mint(alice, 30000, {'from': alice})
    locked_until = (tx.timestamp // 604800 + 13) * 604800
    chain.sleep(604800)
    chain.mine()
    eps_staker.mint(alice, 60000, {'from': alice})

    chain.mine(timestamp=locked_until+1)
    eps_staker.exit({'from': alice})
    assert eps.balanceOf(alice) == initial + 60000
    assert eps_staker.earnedBalances(alice) == [0, []]
    assert eps_staker.unlockedBalance(alice) == 0
    assert eps_staker.totalSupply() == 0


def test_exit_no_penalty(eps, eps_staker, alice):
    initial = eps.balanceOf(alice)
    eps_staker.stake(10000, False, {'from': alice})
    tx = eps_staker.mint(alice, 30000, {'from': alice})
    locked_until = (tx.timestamp // 604800 + 13) * 604800
    chain.sleep(604800)
    chain.mine()
    eps_staker.mint(alice, 60000, {'from': alice})

    chain.mine(timestamp=locked_until+604801)
    eps_staker.exit({'from': alice})
    assert eps.balanceOf(alice) == initial + 90000
    assert eps_staker.earnedBalances(alice) == [0, []]
    assert eps_staker.unlockedBalance(alice) == 0
    assert eps_staker.totalSupply() == 0


def test_locked_gets_penalty(eps, eps_staker, alice, bob):
    initial = eps.balanceOf(alice)
    eps_staker.stake(10**18, True, {'from': alice})
    eps_staker.mint(bob, 100000 * 10**18, {'from': alice})
    eps_staker.exit({'from': bob})
    chain.sleep(604801)
    chain.mine()
    eps_staker.getReward({'from': alice})
    assert (initial + 50000 * 10**18) - eps.balanceOf(alice) < 2 * 10**18


def test_only_locked_gets_penalty(eps, eps_staker, alice, bob):
    eps_staker.stake(10**19, False, {'from': alice})
    eps_staker.stake(10**18, True, {'from': alice})
    eps_staker.stake(10**19, True, {'from': bob})
    chain.sleep(604800)
    chain.mine()
    eps_staker.stake(10**18, True, {'from': alice})
    chain.sleep(604801)
    chain.mine()
    eps_staker.mint(bob, 100000 * 10**18, {'from': alice})
    eps_staker.exit({'from': bob})
    eps_staker.mint(bob, 100000 * 10**18, {'from': alice})
    chain.sleep(604801)
    chain.mine()

    initial_alice = eps.balanceOf(alice)
    initial_bob = eps.balanceOf(bob)

    eps_staker.getReward({'from': alice})
    eps_staker.getReward({'from': bob})

    assert (eps.balanceOf(bob) - initial_bob) / (eps.balanceOf(alice) - initial_alice) == 5.0


def test_get_regular_rewards(eps, eps_staker, alice, bob, token, token2):
    eps_staker.addReward(token, alice, {'from': alice})
    eps_staker.addReward(token2, alice, {'from': alice})
    token.approve(eps_staker, 2**256-1, {'from': alice})
    token2.approve(eps_staker, 2**256-1, {'from': alice})

    eps_staker.stake(10**18, True, {'from': alice})
    eps_staker.stake(5 * 10**18, False, {'from': bob})
    chain.sleep(604800)
    chain.mine()
    eps_staker.stake(10**18, True, {'from': alice})
    eps_staker.mint(bob, 5 * 10**18, {'from': alice})
    chain.sleep(604800)
    chain.mine()

    eps_staker.notifyRewardAmount(token, 100000 * 10**18, {'from': alice})
    eps_staker.notifyRewardAmount(token2, 500000 * 10**18, {'from': alice})
    chain.sleep(604801)
    chain.mine()

    initial_alice = token.balanceOf(alice)
    initial_bob = token.balanceOf(bob)
    initial_alice2 = token2.balanceOf(alice)
    initial_bob2 = token2.balanceOf(bob)

    pending_alice = eps_staker.claimableRewards(alice)
    pending_bob = eps_staker.claimableRewards(bob)

    eps_staker.getReward({'from': alice})
    eps_staker.getReward({'from': bob})

    actual_alice = token.balanceOf(alice) - initial_alice
    actual_alice2 = token2.balanceOf(alice) - initial_alice2
    actual_bob = token.balanceOf(bob) - initial_bob
    actual_bob2 = token2.balanceOf(bob) - initial_bob2

    assert pending_alice == [(eps, 0), (token, actual_alice), (token2, actual_alice2)]
    assert pending_bob == [(eps, 0), (token, actual_bob), (token2, actual_bob2)]

    assert actual_bob / actual_alice == 5.0
    assert actual_bob2 / actual_alice2 == 5.0


def test_regular_and_lock_rewards(eps, eps_staker, alice, bob, token, token2):
    initial_bob_eps = eps.balanceOf(bob)

    eps_staker.addReward(token, alice, {'from': alice})
    eps_staker.addReward(token2, alice, {'from': alice})
    token.approve(eps_staker, 2**256-1, {'from': alice})
    token2.approve(eps_staker, 2**256-1, {'from': alice})

    eps_staker.stake(10**18, True, {'from': alice})
    eps_staker.stake(5 * 10**18, False, {'from': bob})
    chain.sleep(604800)
    chain.mine()
    eps_staker.stake(10**18, True, {'from': alice})
    eps_staker.mint(bob, 5 * 10**18, {'from': alice})
    chain.sleep(604800)
    chain.mine()
    eps_staker.mint(alice, 5 * 10**18, {'from': alice})
    eps_staker.exit({'from': alice})

    eps_staker.notifyRewardAmount(token, 100000 * 10**18, {'from': alice})
    eps_staker.notifyRewardAmount(token2, 500000 * 10**18, {'from': alice})
    chain.sleep(604801)
    chain.mine()

    initial_alice = token.balanceOf(alice)
    initial_bob = token.balanceOf(bob)
    initial_alice2 = token2.balanceOf(alice)
    initial_bob2 = token2.balanceOf(bob)

    initial_alice_eps = eps.balanceOf(alice)

    pending_alice = eps_staker.claimableRewards(alice)

    eps_staker.getReward({'from': alice})
    eps_staker.exit({'from': bob})

    actual_alice_eps = eps.balanceOf(alice) - initial_alice_eps
    actual_alice = token.balanceOf(alice) - initial_alice
    actual_alice2 = token2.balanceOf(alice) - initial_alice2
    assert pending_alice == [(eps, actual_alice_eps), (token, actual_alice), (token2, actual_alice2)]

    assert (token.balanceOf(bob) - initial_bob) / actual_alice == 5.0
    assert (token2.balanceOf(bob) - initial_bob2) / actual_alice2 == 5.0

    assert eps.balanceOf(bob) == initial_bob_eps + (5 * 10**18) // 2
    assert eps.balanceOf(alice) / (initial_alice_eps + (5 * 10**18) // 2) == 1.0


def test_notify_so_many_times(eps, eps_staker, alice, token, token2):
    eps_staker.addReward(token, alice, {'from': alice})
    token.approve(eps_staker, 2**256-1, {'from': alice})

    eps_staker.stake(10**18, True, {'from': alice})

    for i in range(20):
        eps_staker.notifyRewardAmount(token, 10000 * 10**18, {'from': alice})
        chain.sleep(3)

    chain.sleep(604801)
    chain.mine()

    initial_alice = token.balanceOf(alice)
    eps_staker.getReward({'from': alice})

    assert token.balanceOf(alice) / (initial_alice + 200000 * 10**18) == 1.0
