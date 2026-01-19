#!/bin/bash
export PYTHONPATH=$PYTHONPATH:/app

# 1. Start Anvil (Background)
anvil --host 127.0.0.1 --port 8545 &
sleep 5

# 2. Deploy Contract
forge create onchain/contracts/BountyBoard.sol:BountyBoard \
    --rpc-url http://127.0.0.1:8545 \
    --private-key "$PRIVATE_KEY"

# 3. Start Agents
# We run main.py in the background
python3 main.py &

# IMPORTANT: We run the last agent in the FOREGROUND (no &)
# This keeps the container alive as long as this agent is running.
echo "🤖 Starting Strike Bounty Agent..."
python3 onchain/script/strike_bounty.py