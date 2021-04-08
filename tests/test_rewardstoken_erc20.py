
import pytest
import brownie

@pytest.fixture(scope="module")
def token(RewardsToken, alice, lp_staker):
    t = RewardsToken.deploy("LP Token", "LP", lp_staker, {'from': alice})
    t.setMinter(alice, {'from': alice})
    t.mint(alice, 10**21, {'from': alice})
    yield t


@pytest.mark.parametrize("idx", range(5))
def test_initial_approval_is_zero(token, accounts, idx):
    assert token.allowance(accounts[0], accounts[idx]) == 0


def test_approve(token, accounts):
    token.approve(accounts[1], 10**19, {'from': accounts[0]})

    assert token.allowance(accounts[0], accounts[1]) == 10**19


def test_modify_approve(token, accounts):
    token.approve(accounts[1], 10**19, {'from': accounts[0]})
    token.approve(accounts[1], 12345678, {'from': accounts[0]})

    assert token.allowance(accounts[0], accounts[1]) == 12345678


def test_revoke_approve(token, accounts):
    token.approve(accounts[1], 10**19, {'from': accounts[0]})
    token.approve(accounts[1], 0, {'from': accounts[0]})

    assert token.allowance(accounts[0], accounts[1]) == 0


def test_approve_self(token, accounts):
    token.approve(accounts[0], 10**19, {'from': accounts[0]})

    assert token.allowance(accounts[0], accounts[0]) == 10**19


def test_only_affects_target(token, accounts):
    token.approve(accounts[1], 10**19, {'from': accounts[0]})

    assert token.allowance(accounts[1], accounts[0]) == 0


def test_returns_true(token, accounts):
    tx = token.approve(accounts[1], 10**19, {'from': accounts[0]})

    assert tx.return_value is True


def test_approval_event_fires(accounts, token):
    tx = token.approve(accounts[1], 10**19, {'from': accounts[0]})

    assert len(tx.events) == 1
    assert tx.events["Approval"].values() == [accounts[0], accounts[1], 10**19]


def test_sender_balance_decreases(accounts, token):
    sender_balance = token.balanceOf(accounts[0])
    amount = sender_balance // 4

    token.transfer(accounts[1], amount, {'from': accounts[0]})

    assert token.balanceOf(accounts[0]) == sender_balance - amount


def test_receiver_balance_increases(accounts, token):
    receiver_balance = token.balanceOf(accounts[1])
    amount = token.balanceOf(accounts[0]) // 4

    token.transfer(accounts[1], amount, {'from': accounts[0]})

    assert token.balanceOf(accounts[1]) == receiver_balance + amount


def test_total_supply_not_affected(accounts, token):
    total_supply = token.totalSupply()
    amount = token.balanceOf(accounts[0])

    token.transfer(accounts[1], amount, {'from': accounts[0]})

    assert token.totalSupply() == total_supply


def test_transfer_returns_true(accounts, token):
    amount = token.balanceOf(accounts[0])
    tx = token.transfer(accounts[1], amount, {'from': accounts[0]})

    assert tx.return_value is True


def test_transfer_full_balance(accounts, token):
    amount = token.balanceOf(accounts[0])
    receiver_balance = token.balanceOf(accounts[1])

    token.transfer(accounts[1], amount, {'from': accounts[0]})

    assert token.balanceOf(accounts[0]) == 0
    assert token.balanceOf(accounts[1]) == receiver_balance + amount


def test_transfer_zero_tokens(accounts, token):
    sender_balance = token.balanceOf(accounts[0])
    receiver_balance = token.balanceOf(accounts[1])

    token.transfer(accounts[1], 0, {'from': accounts[0]})

    assert token.balanceOf(accounts[0]) == sender_balance
    assert token.balanceOf(accounts[1]) == receiver_balance


def test_transfer_to_self(accounts, token):
    sender_balance = token.balanceOf(accounts[0])
    amount = sender_balance // 4

    token.transfer(accounts[0], amount, {'from': accounts[0]})

    assert token.balanceOf(accounts[0]) == sender_balance


def test_insufficient_balance(accounts, token):
    balance = token.balanceOf(accounts[0])

    with brownie.reverts():
        token.transfer(accounts[1], balance + 1, {'from': accounts[0]})


def test_transfer_event_fires(accounts, token):
    amount = token.balanceOf(accounts[0])
    tx = token.transfer(accounts[1], amount, {'from': accounts[0]})

    assert len(tx.events) == 1
    assert tx.events["Transfer"].values() == [accounts[0], accounts[1], amount]


def test_transfer_from_sender_balance_decreases(accounts, token):
    sender_balance = token.balanceOf(accounts[0])
    amount = sender_balance // 4

    token.approve(accounts[1], amount, {'from': accounts[0]})
    token.transferFrom(accounts[0], accounts[2], amount, {'from': accounts[1]})

    assert token.balanceOf(accounts[0]) == sender_balance - amount


def test_transfer_from_receiver_balance_increases(accounts, token):
    receiver_balance = token.balanceOf(accounts[2])
    amount = token.balanceOf(accounts[0]) // 4

    token.approve(accounts[1], amount, {'from': accounts[0]})
    token.transferFrom(accounts[0], accounts[2], amount, {'from': accounts[1]})

    assert token.balanceOf(accounts[2]) == receiver_balance + amount


def test_caller_balance_not_affected(accounts, token):
    caller_balance = token.balanceOf(accounts[1])
    amount = token.balanceOf(accounts[0])

    token.approve(accounts[1], amount, {'from': accounts[0]})
    token.transferFrom(accounts[0], accounts[2], amount, {'from': accounts[1]})

    assert token.balanceOf(accounts[1]) == caller_balance


def test_caller_approval_affected(accounts, token):
    approval_amount = token.balanceOf(accounts[0])
    transfer_amount = approval_amount // 4

    token.approve(accounts[1], approval_amount, {'from': accounts[0]})
    token.transferFrom(accounts[0], accounts[2], transfer_amount, {'from': accounts[1]})

    assert token.allowance(accounts[0], accounts[1]) == approval_amount - transfer_amount


def test_receiver_approval_not_affected(accounts, token):
    approval_amount = token.balanceOf(accounts[0])
    transfer_amount = approval_amount // 4

    token.approve(accounts[1], approval_amount, {'from': accounts[0]})
    token.approve(accounts[2], approval_amount, {'from': accounts[0]})
    token.transferFrom(accounts[0], accounts[2], transfer_amount, {'from': accounts[1]})

    assert token.allowance(accounts[0], accounts[2]) == approval_amount


def test_transfer_from_total_supply_not_affected(accounts, token):
    total_supply = token.totalSupply()
    amount = token.balanceOf(accounts[0])

    token.approve(accounts[1], amount, {'from': accounts[0]})
    token.transferFrom(accounts[0], accounts[2], amount, {'from': accounts[1]})

    assert token.totalSupply() == total_supply


def test_transfer_from_returns_true(accounts, token):
    amount = token.balanceOf(accounts[0])
    token.approve(accounts[1], amount, {'from': accounts[0]})
    tx = token.transferFrom(accounts[0], accounts[2], amount, {'from': accounts[1]})

    assert tx.return_value is True


def test_transfer_from_full_balance(accounts, token):
    amount = token.balanceOf(accounts[0])
    receiver_balance = token.balanceOf(accounts[2])

    token.approve(accounts[1], amount, {'from': accounts[0]})
    token.transferFrom(accounts[0], accounts[2], amount, {'from': accounts[1]})

    assert token.balanceOf(accounts[0]) == 0
    assert token.balanceOf(accounts[2]) == receiver_balance + amount


def test_transfer_from_zero_tokens(accounts, token):
    sender_balance = token.balanceOf(accounts[0])
    receiver_balance = token.balanceOf(accounts[2])

    token.approve(accounts[1], sender_balance, {'from': accounts[0]})
    token.transferFrom(accounts[0], accounts[2], 0, {'from': accounts[1]})

    assert token.balanceOf(accounts[0]) == sender_balance
    assert token.balanceOf(accounts[2]) == receiver_balance


def test_transfer_zero_tokens_without_approval(accounts, token):
    sender_balance = token.balanceOf(accounts[0])
    receiver_balance = token.balanceOf(accounts[2])

    token.transferFrom(accounts[0], accounts[2], 0, {'from': accounts[1]})

    assert token.balanceOf(accounts[0]) == sender_balance
    assert token.balanceOf(accounts[2]) == receiver_balance


def test_transfer_from_insufficient_balance(accounts, token):
    balance = token.balanceOf(accounts[0])

    token.approve(accounts[1], balance + 1, {'from': accounts[0]})
    with brownie.reverts():
        token.transferFrom(accounts[0], accounts[2], balance + 1, {'from': accounts[1]})


def test_insufficient_approval(accounts, token):
    balance = token.balanceOf(accounts[0])

    token.approve(accounts[1], balance - 1, {'from': accounts[0]})
    with brownie.reverts():
        token.transferFrom(accounts[0], accounts[2], balance, {'from': accounts[1]})


def test_no_approval(accounts, token):
    balance = token.balanceOf(accounts[0])

    with brownie.reverts():
        token.transferFrom(accounts[0], accounts[2], balance, {'from': accounts[1]})


def test_revoked_approval(accounts, token):
    balance = token.balanceOf(accounts[0])

    token.approve(accounts[1], balance, {'from': accounts[0]})
    token.approve(accounts[1], 0, {'from': accounts[0]})

    with brownie.reverts():
        token.transferFrom(accounts[0], accounts[2], balance, {'from': accounts[1]})


def test_transfer_from_to_self(accounts, token):
    sender_balance = token.balanceOf(accounts[0])
    amount = sender_balance // 4

    token.approve(accounts[0], sender_balance, {'from': accounts[0]})
    token.transferFrom(accounts[0], accounts[0], amount, {'from': accounts[0]})

    assert token.balanceOf(accounts[0]) == sender_balance
    assert token.allowance(accounts[0], accounts[0]) == sender_balance - amount


def test_transfer_from_to_self_no_approval(accounts, token):
    amount = token.balanceOf(accounts[0])

    with brownie.reverts():
        token.transferFrom(accounts[0], accounts[0], amount, {'from': accounts[0]})


def test_transfer_from_event_fires(accounts, token):
    amount = token.balanceOf(accounts[0])

    token.approve(accounts[1], amount, {'from': accounts[0]})
    tx = token.transferFrom(accounts[0], accounts[2], amount, {'from': accounts[1]})

    assert len(tx.events) == 1
    assert tx.events["Transfer"].values() == [accounts[0], accounts[2], amount]
