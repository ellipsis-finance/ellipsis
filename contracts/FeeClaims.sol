pragma solidity 0.7.6;


interface IStableSwap {
    function withdraw_admin_fees() external;
}


contract FeeClaimer {

    address owner;
    IStableSwap[] public pools;

    constructor() public {
        owner = msg.sender;
    }

    function claimFees() external {
        for (uint i = 0; i < pools.length; i++) {
            pools[i].withdraw_admin_fees();
        }
    }

    function addPools(IStableSwap[] calldata _pools) external {
        require(msg.sender == owner);
        for (uint i = 0; i < _pools.length; i++) {
            _pools[i].withdraw_admin_fees();
            pools.push(_pools[i]);
        }
    }
}
