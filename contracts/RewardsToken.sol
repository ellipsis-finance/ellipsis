pragma solidity 0.7.6;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";
import "@openzeppelin/contracts/math/Math.sol";
import "@openzeppelin/contracts/math/SafeMath.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";


// LP Token with rewards capability for http://ellipsis.finance/
// ERC20 that represents a deposit into an Ellipsis pool and allows 3rd-party incentives for token holders
// Based on SNX MultiRewards by iamdefinitelyahuman - https://github.com/iamdefinitelyahuman/multi-rewards
contract RewardsToken is ReentrancyGuard, Ownable {

    using SafeMath for uint256;
    using SafeERC20 for IERC20;

    /* ========== STATE VARIABLES ========== */

    string public symbol;
    string public name;
    uint256 public constant decimals = 18;
    uint256 public totalSupply;

    address public lpStaker;
    address public minter;

    struct Reward {
        address rewardsDistributor;
        uint256 rewardsDuration;
        uint256 periodFinish;
        uint256 rewardRate;
        uint256 lastUpdateTime;
        uint256 rewardPerTokenStored;
    }
    mapping(address => Reward) public rewardData;
    address[] public rewardTokens;

    // user -> reward token -> amount
    mapping(address => mapping(address => uint256)) public userRewardPerTokenPaid;
    mapping(address => mapping(address => uint256)) public rewards;

    mapping(address => uint256) public balanceOf;
    mapping(address => uint256) public depositedBalanceOf;

    // owner -> spender -> amount
    mapping(address => mapping(address => uint256)) public allowance;

    /* ========== EVENTS ========== */

    event RewardAdded(uint256 reward);
    event RewardPaid(address indexed user, address indexed rewardsToken, uint256 reward);
    event RewardsDurationUpdated(address token, uint256 newDuration);
    event Recovered(address token, uint256 amount);
    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);

    /* ========== CONSTRUCTOR ========== */

    constructor(
        string memory _name,
        string memory _symbol,
        address _lpStaker
    )
        public Ownable()
    {
        name = _name;
        symbol = _symbol;
        lpStaker = _lpStaker;
        emit Transfer(address(0), msg.sender, 0);
    }

    /* ========== ADMIN FUNCTIONS ========== */

    function addReward(
        address _rewardsToken,
        address _rewardsDistributor,
        uint256 _rewardsDuration
    )
        public
        onlyOwner
    {
        require(rewardData[_rewardsToken].rewardsDuration == 0);
        rewardTokens.push(_rewardsToken);
        rewardData[_rewardsToken].rewardsDistributor = _rewardsDistributor;
        rewardData[_rewardsToken].rewardsDuration = _rewardsDuration;
    }

    function setRewardsDistributor(address _rewardsToken, address _rewardsDistributor) external onlyOwner {
        rewardData[_rewardsToken].rewardsDistributor = _rewardsDistributor;
    }

    function setMinter(address _minter) external {
        require(minter == address(0));
        minter = _minter;
    }

    /* ========== MODIFIERS ========== */

    modifier updateReward(address payable[2] memory accounts) {
        address _lpStaker = lpStaker;
        for (uint i; i < rewardTokens.length; i++) {
            address token = rewardTokens[i];
            rewardData[token].rewardPerTokenStored = rewardPerToken(token);
            rewardData[token].lastUpdateTime = lastTimeRewardApplicable(token);
            for (uint x = 0; x < accounts.length; x++) {
                address account = accounts[x];
                if (account == address(0)) break;
                if (account == _lpStaker) continue;
                rewards[account][token] = earned(account, token);
                userRewardPerTokenPaid[account][token] = rewardData[token].rewardPerTokenStored;
            }
        }
        _;
    }

    /* ========== VIEWS ========== */

    function lastTimeRewardApplicable(address _rewardsToken) public view returns (uint256) {
        return Math.min(block.timestamp, rewardData[_rewardsToken].periodFinish);
    }

    function rewardPerToken(address _rewardsToken) public view returns (uint256) {
        Reward storage reward = rewardData[_rewardsToken];
        if (totalSupply == 0) {
            return reward.rewardPerTokenStored;
        }
        uint256 last = lastTimeRewardApplicable(_rewardsToken);
        return reward.rewardPerTokenStored.add(
            last.sub(reward.lastUpdateTime).mul(reward.rewardRate).mul(1e18).div(totalSupply)
        );
    }

    function earned(address account, address _rewardsToken) public view returns (uint256) {
        if (account == lpStaker) return 0;
        uint256 balance = balanceOf[account].add(depositedBalanceOf[account]);
        uint256 perToken = rewardPerToken(_rewardsToken).sub(userRewardPerTokenPaid[account][_rewardsToken]);
        return balance.mul(perToken).div(1e18).add(rewards[account][_rewardsToken]);
    }

    function getRewardForDuration(address _rewardsToken) external view returns (uint256) {
        return rewardData[_rewardsToken].rewardRate.mul(rewardData[_rewardsToken].rewardsDuration);
    }

    /* ========== MUTATIVE FUNCTIONS ========== */

    function approve(address _spender, uint256 _value) public returns (bool) {
        allowance[msg.sender][_spender] = _value;
        emit Approval(msg.sender, _spender, _value);
        return true;
    }

    /** shared logic for transfer and transferFrom */
    function _transfer(
        address payable _from,
        address payable _to,
        uint256 _value
    )
        internal
        updateReward([_from, _to])
    {
        require(balanceOf[_from] >= _value, "Insufficient balance");
        balanceOf[_from] = balanceOf[_from].sub(_value);
        balanceOf[_to] = balanceOf[_to].add(_value);

        // for transfers into or out of LpTokenStaker, modify depositedBalance
        if (_to == lpStaker) {
            depositedBalanceOf[_from] = depositedBalanceOf[_from].add(_value);
        } else if (_from == lpStaker) {
            depositedBalanceOf[_to] = depositedBalanceOf[_to].sub(_value);
        }
        emit Transfer(_from, _to, _value);
    }

    function transfer(address payable _to, uint256 _value) public returns (bool) {
        _transfer(msg.sender, _to, _value);
        return true;
    }

    function transferFrom(
        address payable _from,
        address payable _to,
        uint256 _value
    )
        public
        returns (bool)
    {
        uint256 allowed = allowance[_from][msg.sender];
        require(allowed >= _value, "Insufficient allowance");
        if (allowed != uint256(-1)) {
            allowance[_from][msg.sender] = allowed.sub(_value);
        }
        _transfer(_from, _to, _value);
        return true;
    }

    function getReward() public nonReentrant updateReward([msg.sender, address(0)]) {
        for (uint i; i < rewardTokens.length; i++) {
            address _rewardsToken = rewardTokens[i];
            uint256 reward = rewards[msg.sender][_rewardsToken];
            if (reward > 0) {
                rewards[msg.sender][_rewardsToken] = 0;
                IERC20(_rewardsToken).safeTransfer(msg.sender, reward);
                emit RewardPaid(msg.sender, _rewardsToken, reward);
            }
        }
    }

    /* ========== RESTRICTED FUNCTIONS ========== */

    function notifyRewardAmount(
        address _rewardsToken,
        uint256 reward
    )
        external
        updateReward([address(0), address(0)])
    {
        require(rewardData[_rewardsToken].rewardsDistributor == msg.sender);
        // handle the transfer of reward tokens via `transferFrom` to reduce the number
        // of transactions required and ensure correctness of the reward amount
        IERC20(_rewardsToken).safeTransferFrom(msg.sender, address(this), reward);

        if (block.timestamp >= rewardData[_rewardsToken].periodFinish) {
            rewardData[_rewardsToken].rewardRate = reward.div(rewardData[_rewardsToken].rewardsDuration);
        } else {
            uint256 remaining = rewardData[_rewardsToken].periodFinish.sub(block.timestamp);
            uint256 leftover = remaining.mul(rewardData[_rewardsToken].rewardRate);
            rewardData[_rewardsToken].rewardRate = reward.add(leftover).div(rewardData[_rewardsToken].rewardsDuration);
        }

        rewardData[_rewardsToken].lastUpdateTime = block.timestamp;
        rewardData[_rewardsToken].periodFinish = block.timestamp.add(rewardData[_rewardsToken].rewardsDuration);
        emit RewardAdded(reward);
    }

    // Added to support recovering LP Rewards from other systems such as BAL to be distributed to holders
    function recoverERC20(address tokenAddress, uint256 tokenAmount) external onlyOwner {
        require(rewardData[tokenAddress].lastUpdateTime == 0, "Cannot withdraw reward token");
        IERC20(tokenAddress).safeTransfer(owner(), tokenAmount);
        emit Recovered(tokenAddress, tokenAmount);
    }

    function setRewardsDuration(address _rewardsToken, uint256 _rewardsDuration) external {
        require(
            block.timestamp > rewardData[_rewardsToken].periodFinish,
            "Reward period still active"
        );
        require(rewardData[_rewardsToken].rewardsDistributor == msg.sender);
        require(_rewardsDuration > 0, "Reward duration must be non-zero");
        rewardData[_rewardsToken].rewardsDuration = _rewardsDuration;
        emit RewardsDurationUpdated(_rewardsToken, rewardData[_rewardsToken].rewardsDuration);
    }

    function mint(
        address payable _to,
        uint256 _value
    )
        external
        updateReward([_to, address(0)])
        returns (bool)
    {
        require(msg.sender == minter);
        balanceOf[_to] = balanceOf[_to].add(_value);
        totalSupply = totalSupply.add(_value);
        emit Transfer(address(0), _to, _value);
        return true;
    }

    function burnFrom(
        address payable _to,
        uint256 _value
    )
        external
        updateReward([_to, address(0)])
        returns (bool)
    {
        require(msg.sender == minter);
        balanceOf[_to] = balanceOf[_to].sub(_value);
        totalSupply = totalSupply.sub(_value);
        emit Transfer(_to, address(0), _value);
        return true;
    }
}
