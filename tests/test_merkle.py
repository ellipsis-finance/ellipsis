import brownie
from eth_abi.packed import encode_abi_packed
from eth_utils import encode_hex
from brownie import web3
from itertools import zip_longest
import pytest

class MerkleTree:
    def __init__(self, elements):
        self.elements = sorted(set(web3.keccak(hexstr=el) for el in elements))
        self.layers = MerkleTree.get_layers(self.elements)

    @property
    def root(self):
        return self.layers[-1][0]

    def get_proof(self, el):
        el = web3.keccak(hexstr=el)
        idx = self.elements.index(el)
        proof = []
        for layer in self.layers:
            pair_idx = idx + 1 if idx % 2 == 0 else idx - 1
            if pair_idx < len(layer):
                proof.append(encode_hex(layer[pair_idx]))
            idx //= 2
        return proof

    @staticmethod
    def get_layers(elements):
        layers = [elements]
        while len(layers[-1]) > 1:
            layers.append(MerkleTree.get_next_layer(layers[-1]))
        return layers

    @staticmethod
    def get_next_layer(elements):
        return [MerkleTree.combined_hash(a, b) for a, b in zip_longest(elements[::2], elements[1::2])]

    @staticmethod
    def combined_hash(a, b):
        if a is None:
            return b
        if b is None:
            return a
        return web3.keccak(b''.join(sorted([a, b])))


@pytest.fixture(scope="module")
def distribution(accounts):
    balances = {i.address: c*10**18 for c, i in enumerate(accounts, start=1)}
    elements = [(index, account, amount) for index, (account, amount) in enumerate(balances.items())]
    nodes = [encode_hex(encode_abi_packed(['uint', 'address', 'uint'], el)) for el in elements]
    tree = MerkleTree(nodes)
    return {
        'merkleRoot': encode_hex(tree.root),
        'tokenTotal': hex(sum(balances.values())),
        'claims': {
            user: {'index': index, 'amount': hex(amount), 'proof': tree.get_proof(nodes[index])}
            for index, user, amount in elements
        },
    }


@pytest.fixture(scope="module")
def distribution2(accounts):
    balances = {i.address: c*2*10**18 for c, i in enumerate(accounts, start=1)}
    elements = [(index, account, amount) for index, (account, amount) in enumerate(balances.items())]
    nodes = [encode_hex(encode_abi_packed(['uint', 'address', 'uint'], el)) for el in elements]
    tree = MerkleTree(nodes)
    return {
        'merkleRoot': encode_hex(tree.root),
        'tokenTotal': hex(sum(balances.values())),
        'claims': {
            user: {'index': index, 'amount': hex(amount), 'proof': tree.get_proof(nodes[index])}
            for index, user, amount in elements
        },
    }


@pytest.fixture(scope="module")
def distribution3(accounts):
    balances = {i.address: c*3*10**18 for c, i in enumerate(accounts, start=1)}
    elements = [(index, account, amount) for index, (account, amount) in enumerate(balances.items())]
    nodes = [encode_hex(encode_abi_packed(['uint', 'address', 'uint'], el)) for el in elements]
    tree = MerkleTree(nodes)
    return {
        'merkleRoot': encode_hex(tree.root),
        'tokenTotal': hex(sum(balances.values())),
        'claims': {
            user: {'index': index, 'amount': hex(amount), 'proof': tree.get_proof(nodes[index])}
            for index, user, amount in elements
        },
    }


def test_distribution(distribution, merkle, eps_staker, accounts, alice, bob):
    merkle.proposewMerkleRoot(distribution['merkleRoot'], {'from': alice})
    merkle.reviewPendingMerkleRoot(True, {'from': bob})
    for acct, claim in distribution['claims'].items():
        merkle.claim(0, claim['index'], claim['amount'], claim['proof'], {'from': acct})
        assert eps_staker.totalBalance(acct) == claim['amount']
        with brownie.reverts('MerkleDistributor: Drop already claimed.'):
            merkle.claim(0, claim['index'], claim['amount'], claim['proof'], {'from': acct})


def test_multiple_distributions(chain, alice, bob, distribution, distribution2, distribution3, merkle, eps_staker, accounts):
    with brownie.reverts():
        merkle.reviewPendingMerkleRoot(True, {'from': bob})
    merkle.proposewMerkleRoot(distribution['merkleRoot'], {'from': alice})
    with brownie.reverts():
        merkle.proposewMerkleRoot(distribution2['merkleRoot'], {'from': alice})
    merkle.reviewPendingMerkleRoot(True, {'from': bob})
    chain.sleep(604801)
    chain.mine()
    merkle.proposewMerkleRoot(distribution2['merkleRoot'], {'from': alice})
    merkle.reviewPendingMerkleRoot(True, {'from': bob})
    with brownie.reverts():
        merkle.proposewMerkleRoot(distribution2['merkleRoot'], {'from': alice})
    chain.sleep(604801)
    chain.mine()
    merkle.proposewMerkleRoot(distribution3['merkleRoot'], {'from': alice})
    merkle.reviewPendingMerkleRoot(True, {'from': bob})
    for acct, claim in distribution['claims'].items():
        merkle.claim(0, claim['index'], claim['amount'], claim['proof'], {'from': acct})
        assert eps_staker.totalBalance(acct) == claim['amount']
        eps_staker.exit({'from': acct})
        with brownie.reverts('MerkleDistributor: Drop already claimed.'):
            merkle.claim(0, claim['index'], claim['amount'], claim['proof'], {'from': acct})
    for acct, claim in distribution2['claims'].items():
        merkle.claim(1, claim['index'], claim['amount'], claim['proof'], {'from': acct})
        assert eps_staker.totalBalance(acct) == claim['amount']
        eps_staker.exit({'from': acct})
        with brownie.reverts('MerkleDistributor: Drop already claimed.'):
            merkle.claim(1, claim['index'], claim['amount'], claim['proof'], {'from': acct})
        with brownie.reverts('MerkleDistributor: Invalid proof.'):
            merkle.claim(2, claim['index'], claim['amount'], claim['proof'], {'from': acct})
    for acct, claim in distribution3['claims'].items():
        merkle.claim(2, claim['index'], claim['amount'], claim['proof'], {'from': acct})
        assert eps_staker.totalBalance(acct) == claim['amount']
        eps_staker.exit({'from': acct})
        with brownie.reverts('MerkleDistributor: Invalid merkleIndex'):
            merkle.claim(3, claim['index'], claim['amount'], claim['proof'], {'from': acct})
