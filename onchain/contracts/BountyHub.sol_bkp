// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract BountyHub {
    struct Proof {
        address agent;
        uint256 timestamp;
        bool revealed;
        string metadata; // Store repo/vuln type after reveal
    }

    // Maps the hash (commitment) to the Proof details
    mapping(bytes32 => Proof) public commitments;

    event FindingCommitted(address indexed agent, bytes32 indexed commitHash);
    event FindingRevealed(address indexed agent, bytes32 indexed commitHash, string details);

    /**
     * @dev Step 1: Agent commits the hash of (repo + file + vuln + salt)
     */
    function commitFinding(bytes32 _commitHash) external {
        require(commitments[_commitHash].agent == address(0), "Commitment already exists");
        
        commitments[_commitHash] = Proof({
            agent: msg.sender,
            timestamp: block.timestamp,
            revealed: false,
            metadata: ""
        });

        emit FindingCommitted(msg.sender, _commitHash);
    }

    /**
     * @dev Step 2: After PR is merged, agent reveals the plain text and salt
     */
    function revealFinding(
        string memory _repo, 
        string memory _file, 
        string memory _vuln, 
        string memory _salt
    ) external {
        // Recreate the hash locally to verify the reveal
        bytes32 revealHash = keccak256(abi.encodePacked(_repo, ":", _file, ":", _vuln, ":", _salt));
        
        Proof storage p = commitments[revealHash];
        require(p.agent == msg.sender, "Only the original agent can reveal");
        require(!p.revealed, "Already revealed");

        p.revealed = true;
        p.metadata = string(abi.encodePacked(_repo, " | ", _vuln));

        emit FindingRevealed(msg.sender, revealHash, p.metadata);
    }
}