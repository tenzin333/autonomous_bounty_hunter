import os
from web3 import Web3
from core.config import Config

w3 = Web3(Web3.HTTPProvider(Config.RPC_URL))

address = Config.CONTRACT_ADDRESS

# Simple ABI for just the create function
abi = Config.ABI_PATH

contract = w3.eth.contract(address=address, abi=abi)

# The "Puzzle": Hash of the word 'orange'
secret_word = "orange"
target_hash = w3.keccak(text=secret_word)

def post_bounty():
    acct = w3.eth.accounts[1] # Use a different account than the hunter
    tx = contract.functions.createBounty(target_hash).transact({
        'from': acct,
        'value': w3.to_wei(1, 'ether')
    })
    print(f"💰 Bounty Posted! Hash: {target_hash.hex()}")
    print(f"TX: {tx.hex()}")

if __name__ == "__main__":
    post_bounty()
