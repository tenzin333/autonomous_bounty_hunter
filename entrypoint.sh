#!/bin/bash

# 1. Start Anvil in background (internal only)
anvil --host 127.0.0.1 --port 8545 &
sleep 5

# 2. Deploy Contract
forge script onchain/contracts/BountyBoard.sol:BountyBoard \
    --rpc-url http://127.0.0.1:8545 \
    --broadcast \
    --private-key "$PRIVATE_KEY"

# 3. Launch Python Agents (main.py must include the Flask server)
python3 main.py &
python3 onchain/script/strikerbounty.py &

# Wait for processes
wait -n