// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title BountyBoard
 * @dev A realistic autonomous bounty board where rewards are released 
 * upon providing a cryptographic preimage (the secret).
 */
contract BountyBoard {
    struct Bounty {
        address creator;
        uint256 reward;
        bytes32 targetHash; // The SHA-3 hash of the "answer"
        bool active;
    }

    mapping(uint256 => Bounty) public bounties;
    uint256 public bountyCount;

    event BountyCreated(uint256 indexed id, uint256 reward, bytes32 targetHash);
    event BountyClaimed(uint256 indexed id, address indexed winner, uint256 reward);

    /// @notice Create a bounty by sending ETH and a hash of the solution.
    function createBounty(bytes32 _targetHash) external payable {
        require(msg.value > 0, "Must provide a reward");
        
        bountyCount++;
        bounties[bountyCount] = Bounty({
            creator: msg.sender,
            reward: msg.value,
            targetHash: _targetHash,
            active: true
        });

        emit BountyCreated(bountyCount, msg.value, _targetHash);
    }

    /// @notice Claim a bounty by providing the string that matches the targetHash.
    function claimBounty(uint256 _id, string memory _secret) external {
        Bounty storage b = bounties[_id];
        
        require(b.active, "Bounty not active or already claimed");
        // Verify the secret: hash(secret) == targetHash
        require(keccak256(abi.encodePacked(_secret)) == b.targetHash, "Invalid secret");

        uint256 rewardAmount = b.reward;
        b.active = false; // "Checks-Effects-Interactions" pattern to prevent reentrancy
        b.reward = 0;

        (bool success, ) = payable(msg.sender).call{value: rewardAmount}("");
        require(success, "Transfer failed");

        emit BountyClaimed(_id, msg.sender, rewardAmount);
    }

    // Allow the contract to receive ETH
    receive() external payable {}
}
