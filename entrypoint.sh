#!/bin/bash
export PYTHONPATH=$PYTHONPATH:/app

# 1. Start Anvil in the background
anvil --host 127.0.0.1 --port 8545 &
ANVIL_PID=$! # Capture the process ID
sleep 5

# 2. Deploy Contract
echo "🚀 Deploying Contract..."
forge create onchain/contracts/BountyBoard.sol:BountyBoard \
  --rpc-url http://127.0.0.1:8545 \
  --private-key 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80 \
  --broadcast

# 3. Start Agent in the background
echo "🤖 Starting main.py..."
python3 main.py &
AGENT_PID=$!

# 4. Run bounty claim in the foreground
# This runs after the agent is already up and listening
echo "💰 Running bounty claim..."
python3 onchain/script/strike_bounty.py

# 5. PREVENT EXIT
# This waits for the background agent (main.py) to finish.
# If main.py is a long-running service, the container stays alive.
wait $AGENT_PID