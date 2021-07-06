pragma solidity 0.7.6;


interface IStableSwap {
    function withdraw_admin_fees() external;
}


contract FeeClaimer {

    address owner;
    IStableSwap[] public pools;

    event FeeClaimSuccess(IStableSwap pool);
    event FeeClaimRevert(IStableSwap pool);

    constructor() public {
        owner = msg.sender;
    }

    function claimFees() external {
        for (uint i = 0; i < pools.length; i++) {
            IStableSwap pool = pools[i];
            try pool.withdraw_admin_fees() {
                emit FeeClaimSuccess(pool);
            } catch {
                emit FeeClaimRevert(pool);
            }
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
