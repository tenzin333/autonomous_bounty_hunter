import json
from web3 import Web3
from core.config import Config

# 🔌 Connect
w3 = Web3(Web3.HTTPProvider(Config.RPC_URL))

# 📜 Load ABI
try:
    with open(Config.ABI_PATH, "r") as f:
        artifact = json.load(f)
        
        # Extract the ABI correctly from the Foundry dictionary
        if isinstance(artifact, dict) and "abi" in artifact:
            contract_abi = artifact["abi"]
        else:
            contract_abi = artifact  # Fallback if it's already a list
except Exception as e:
    raise Exception(f"Failed to parse ABI JSON: {e}")


contract = w3.eth.contract(address=Config.CONTRACT_ADDRESS, abi=contract_abi)

def strike_bounty(bounty_id: int, secret: str):
    print(f"Striking Bounty #{bounty_id}...")

    # 🔑 1. Setup Account
    hunter_account = w3.eth.account.from_key(Config.PRIVATE_KEY)
    
    # 🧱 2. Build Modern (EIP-1559) Transaction
    # We use 'maxFeePerGas' instead of 'gasPrice' for modern chains
    tx = contract.functions.claimBounty(bounty_id, secret).build_transaction({
        "from": hunter_account.address,
        "nonce": w3.eth.get_transaction_count(hunter_account.address),
        "gas": 250000,
        "maxFeePerGas": w3.to_wei("2", "gwei"),
        "maxPriorityFeePerGas": w3.to_wei("1", "gwei"),
        "chainId": w3.eth.chain_id # Dynamically get chain ID
    })

    # ✍️ 3. Sign Transaction
    signed_tx = w3.eth.account.sign_transaction(tx, private_key=Config.PRIVATE_KEY)

    # 📡 4. Send Transaction (Broadcasting)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"📡 Transaction Sent! Hash: {tx_hash.hex()}")

    # ⏳ 5. Wait for Receipt (Proof it worked)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    if receipt.status == 1:
        print(f"Successfully claimed bounty #{bounty_id}!")
    else:
        print(f"Transaction failed. Check your secret or bounty ID.")
    
    return tx_hash.hex()

if __name__ == "__main__":
    # Example test call
    # strike_bounty(1, "my_secret_patch_hash")
    pass