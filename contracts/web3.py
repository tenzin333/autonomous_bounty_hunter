from web3 import Web3

class BlockchainLogger:
    def __init__(self, provider_url, private_key):
        self.w3 = Web3(Web3.HTTPProvider(provider_url))
        self.account = self.w3.eth.account.from_key(private_key)
        
    def log_finding(self, repo_url, file_path, vuln_type):
        # 1. Generate the hash
        raw_data = f"{repo_url}:{file_path}:{vuln_type}:{self.salt}"
        finding_hash = self.w3.keccak(text=raw_data)

        # 2. Build the transaction
        # Note: 'contract' would be initialized with the ABI and Address
        tx = self.contract.functions.commitFinding(finding_hash).build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'gas': 200000,
            'gasPrice': self.w3.to_wei('50', 'gwei')
        })

        # 3. Sign and Send
        signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=self.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        return tx_hash.hex()

# In main.py:
# logger = BlockchainLogger(Config.RPC_URL, Config.AGENT_PRIVATE_KEY)
# proof = logger.log_finding(target_repo, "job-schema.js", "ReDoS")