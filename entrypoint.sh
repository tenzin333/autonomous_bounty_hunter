#!/bin/bash

# 1. Start Anvil
anvil --host 127.0.0.1 --port 8545 &
sleep 5

# 2. Fix Foundry Artifacts & Deploy
forge clean
# Replace 'BountyBoard' with the actual Script name if it's different
echo "🚀 Deploying Contract..."
forge create onchain/contracts/BountyBoard.sol:BountyBoard \
    --rpc-url http://127.0.0.1:8545 \
    --private-key "$PRIVATE_KEY"

# 3. Start Agents (Using relative paths from /app)
# Check if your file is actually at 'onchain/script/strikerbounty.py'
echo "🤖 Starting Agents..."
python3 main.py &
python3 onchain/script/strike_bounty.py &

wait -n