#!/bin/bash
export PYTHONPATH=$PYTHONPATH:/app

# 1. Start Anvil
anvil --host 127.0.0.1 --port 8545 &
sleep 5

# 2. Deploy Contract (One solid line to avoid backslash errors)
echo "🚀 Deploying Contract..."
forge create onchain/contracts/BountyBoard.sol:BountyBoard --rpc-url http://127.0.0.1:8545 --private-key 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80 --broadcast

# 3. Start Agents
echo "🤖 Starting main.py..."
# Use '&' to run in background
python3 main.py &

# 4. PREVENT EXIT
# This is the most important part! 
# We use 'wait' so the container stays open while main.py runs.
wait