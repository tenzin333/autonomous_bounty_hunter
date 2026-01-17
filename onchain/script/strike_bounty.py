import sys
from web3 import Web3
from core.config import Config
from pathlib import Path
import json


# 🔌 Connect to local chain (Anvil / Hardhat)
w3 = Web3(Web3.HTTPProvider(Config.RPC_URL))

# 📜 Load ABI
ABI_PATH = Config.ABI_PATH
with open(ABI_PATH, "r") as f:
    contract_abi = json.load(f)

# 🧱 Contract object
contract = w3.eth.contract(
    address=Config.CONTRACT_ADDRESS,
    abi=contract_abi
)

def strike_bounty(bounty_id: int, secret: str):
    print(f"🚀 Striking Bounty #{bounty_id}...")

    # 🔑 1. Hunter private key
    hunter_key = Config.PRIVATE_KEY
    hunter_account = w3.eth.account.from_key(hunter_key)

    # 🧱 2. Build tx
    nonce = w3.eth.get_transaction_count(hunter_account.address)
    tx = contract.functions.claimBounty(bounty_id, secret).build_transaction({
        "from": hunter_account.address,
        "nonce": nonce,
        "gas": 200000,
        "maxFeePerGas": w3.to_wei("2", "gwei"),
        "maxPriorityFeePerGas": w3.to_wei("1", "gwei"),
        "value": 0
    })

    # ✍️ 3. Sign
    signed_tx = w3.eth.accoun_
