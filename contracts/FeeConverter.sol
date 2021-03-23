pragma solidity 0.7.6;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";

interface IStableSwap {
    function exchange(int128 i, int128 j, uint dx, uint min_dy) external;
    function coins(uint i) external returns (IERC20);
}

interface IMultiFeeDistribution {
    function notifyRewardAmount(IERC20 rewardsToken, uint256 reward) external;
}

contract FeeConverter {
    using SafeERC20 for IERC20;

    address public feeDistributor;

    function setFeeDistributor(address distributor) external {
        require (feeDistributor == address(0));
        feeDistributor = distributor;
    }

    function convertFees(uint i, uint j) external {
        IERC20 inputCoin = IStableSwap(msg.sender).coins(i);
        IERC20 outputCoin = IStableSwap(msg.sender).coins(j);

        uint256 balance = inputCoin.balanceOf(address(this));
        inputCoin.safeApprove(msg.sender, balance);
        IStableSwap(msg.sender).exchange(int128(i), int128(j), balance, 0);
    }

    function notify(IERC20 coin) external {
        uint256 balance = coin.balanceOf(address(this));
        coin.safeApprove(feeDistributor, balance);
        IMultiFeeDistribution(feeDistributor).notifyRewardAmount(coin, balance);
    }

}
