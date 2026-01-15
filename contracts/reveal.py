import os
import json
from web3 import Web3
from core.config import Config
from core.database import HunterDB # Assuming you have a DB to track findings

class BountyRevealer:
    def __init__(self):
        # 1. Use RPC_URL from your centralized config
        self.w3 = Web3(Web3.HTTPProvider(Config.RPC_URL))
        
        # 2. Never hardcode private keys; pull from environment/config
        self.account = self.w3.eth.account.from_key(Config.AGENT_PRIVATE_KEY)
        
        # 3. Pull contract address and salt from config
        self.contract = self.w3.eth.contract(
            address=Config.CONTRACT_ADDRESS, 
            abi=Config.BOUNTY_HUB_ABI # Store your ABI in a JSON file or Config
        )
        self.salt = Config.COMMITMENT_SALT

    def reveal_finding(self, repo, file, vuln):
        print(f"Attempting to reveal finding for: {repo}")
        
        try:
            # Build the transaction dynamically
            tx = self.contract.functions.revealFinding(
                repo, file, vuln, self.salt
            ).build_transaction({
                'from': self.account.address,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'gas': 300000,
                'gasPrice': self.w3.eth.gas_price
            })

            signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            print(f"Transaction Sent! Hash: {tx_hash.hex()}")
            return tx_hash.hex()
            
        except Exception as e:
            print(f"Failed to reveal finding: {e}")
            return None

if __name__ == "__main__":
    # In production, we iterate through 'Ready to Reveal' items in our database
    db = HunterDB()
    pending_reveals = db.get_merged_pull_requests() # Method to find merged but unrevealed bugs

    revealer = BountyRevealer()
    
    for bug in pending_reveals:
        revealer.reveal_finding(
            repo=bug['repo'],
            file=bug['file'],
            vuln=bug['vuln_type']
        )