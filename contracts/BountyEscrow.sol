// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";

contract BountyEscrow is Ownable {
    struct Bounty {
        uint256 amount;
        string repoFullName; // e.g., "owner/repo"
        uint256 prNumber;
        address payable hunter;
        bool claimed;
    }

    mapping(bytes32 => Bounty) public bounties; // Hashed ID -> Bounty detail

    event BountyDeposited(bytes32 indexed bountyId, uint256 amount);
    event BountyClaimed(bytes32 indexed bountyId, address hunter);

    constructor() Ownable(msg.sender) {}

    // 1. Owner deposits funds for a specific bug hunt
    function createBounty(string memory _repo, uint256 _prNum, bytes32 _bountyId) external payable onlyOwner {
        require(msg.value > 0, "Bounty must be > 0");
        bounties[_bountyId] = Bounty(msg.value, _repo, _prNum, payable(address(0)), false);
        emit BountyDeposited(_bountyId, msg.value);
    }

    // 2. Oracle (Chainlink/Backend) calls this after verifying the PR is MERGED
    function fulfillBounty(bytes32 _bountyId, address payable _hunter) external onlyOwner {
        Bounty storage bounty = bounties[_bountyId];
        require(!bounty.claimed, "Already paid");
        require(address(this).balance >= bounty.amount, "Insufficient contract balance");

        bounty.claimed = true;
        bounty.hunter = _hunter;
        
        (bool success, ) = _hunter.call{value: bounty.amount}("");
        require(success, "Transfer failed");

        emit BountyClaimed(_bountyId, _hunter);
    }
}