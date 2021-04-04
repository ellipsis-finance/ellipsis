import pytest
from brownie_tokens import ERC20
from brownie import compile_source


@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass


@pytest.fixture(scope="session")
def alice(accounts):
    yield accounts[0]


@pytest.fixture(scope="session")
def bob(accounts):
    yield accounts[1]


@pytest.fixture(scope="session")
def charlie(accounts):
    yield accounts[2]


@pytest.fixture(scope="module")
def pool2token(alice, bob):
    contract = ERC20()
    contract._mint_for_testing(alice, 1000000 * 10**18)
    contract._mint_for_testing(bob, 1000000 * 10**18)
    yield contract


@pytest.fixture(scope="module")
def token(alice, bob):
    contract = ERC20()
    contract._mint_for_testing(alice, 1000000 * 10**18)
    contract._mint_for_testing(bob, 1000000 * 10**18)
    yield contract


@pytest.fixture(scope="module")
def token2(alice, bob):
    contract = ERC20()
    contract._mint_for_testing(alice, 1000000 * 10**18)
    contract._mint_for_testing(bob, 1000000 * 10**18)
    yield contract


@pytest.fixture(scope="module")
def lp_staker(LpTokenStaker, alice, bob, token, pool2token):
    offsets = [1000, 2000, 3000]
    rewards_per_second = [10000000000000, 5000000000000, 0]
    contract = LpTokenStaker.deploy(offsets, rewards_per_second, pool2token, {"from": alice})
    contract.addPool(token, 0, {'from': alice})
    token.approve(contract, 2**256-1, {'from': alice})
    token.approve(contract, 2**256-1, {'from': bob})
    pool2token.approve(contract, 2**256-1, {'from': alice})
    contract.start({'from': alice})
    yield contract


@pytest.fixture(scope="module")
def fee_converter(FeeConverter, alice):
    yield FeeConverter.deploy({"from": alice})


@pytest.fixture(scope="module")
def eps(Token, alice, bob):
    contract = Token.deploy("Ellipsis", "EPS", 1000000 * 10**18, {"from": alice})
    contract.transfer(bob, 500000 * 10**18, {'from': alice})

    yield contract


@pytest.fixture(scope="module")
def eps_staker(MultiFeeDistribution, alice, bob, lp_staker, eps, fee_converter, merkle):
    contract = MultiFeeDistribution.deploy(eps, [lp_staker, merkle, alice], {"from": alice})
    lp_staker.setMinter(contract, {"from": alice})
    eps.set_minter(contract, {'from': alice})
    fee_converter.setFeeDistributor(contract, {"from": alice})
    merkle.setMinter(contract, {'from': alice})
    eps.approve(contract, 2**256-1, {'from': alice})
    eps.approve(contract, 2**256-1, {'from': bob})
    yield contract


@pytest.fixture(scope="module")
def oracle(alice):
    yield compile_source("""
pragma solidity 0.7.6;
contract Oracle {

    int256 public latestAnswer;

    function setAnswer(int256 answer) external {
        latestAnswer = answer;
    }
}
    """).Oracle.deploy({'from': alice})


@pytest.fixture(scope="module")
def merkle(MerkleDistributor, alice, bob):
    yield MerkleDistributor.deploy(alice, bob, {'from': alice})
