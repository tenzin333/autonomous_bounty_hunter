from web3 import Web3
from core.config import Config
import json

class BlockchainLogger:
    def __init__(self, provider_url, private_key, contract_address, contract_abi_path):
        self.w3 = Web3(Web3.HTTPProvider(provider_url))

        if not self.w3.is_connected():
            raise RuntimeError("Web3 provider connection failed")

        self.account = self.w3.eth.account.from_key(private_key)
        self.private_key = private_key
        self.salt = Config.COMMITMENT_SALT

        # Load ABI JSON from fil
		# --- THE FIX IS HERE ---
        try:
            with open(contract_abi_path, "r") as f:
                artifact = json.load(f)
                
                # Extract the ABI correctly from the Foundry dictionary
                if isinstance(artifact, dict) and "abi" in artifact:
                    self.abi = artifact["abi"]
                else:
                    self.abi = artifact  # Fallback if it's already a list
        except Exception as e:
            raise Exception(f"Failed to parse ABI JSON: {e}")
        # -----------------------e
        
		# Create contract instance
        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(contract_address),
            abi=self.abi
        )

    def log_finding(self, repo_url, file_path, vuln_type):
        raw_data = f"{repo_url}:{file_path}:{vuln_type}:{self.salt}"
        finding_hash = self.w3.keccak(text=raw_data)

        tx = self.contract.functions.createBounty(finding_hash).build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'gas': 200000,
            'gasPrice': self.w3.to_wei('50', 'gwei')
        })

        signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=self.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)

        return tx_hash.hex()

