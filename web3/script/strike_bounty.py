from core.config import Config




def strike_bounty(bounty_id, secret):
    print(f"🚀 Striking Bounty #{bounty_id}...")
    
    # 1. Get the account from the private key in .env
    hunter_key =  Config.PRIVATE_KEY
    hunter_account = w3.eth.account.from_key(hunter_key)
    
    # 2. Build the transaction
    # We call the 'claimBounty' function from your Solidity contract
    nonce = w3.eth.get_transaction_count(hunter_account.address)
    
    tx = contract.functions.claimBounty(bounty_id, secret).build_transaction({
        'from': hunter_account.address,
        'nonce': nonce,
        'gas': 200000,
        'maxFeePerGas': w3.to_wei('2', 'gwei'),
        'maxPriorityFeePerGas': w3.to_wei('1', 'gwei'),
    })

    # 3. Sign the transaction
    signed_tx = w3.eth.account.sign_transaction(tx, private_key=hunter_key)

    # 4. Send it to the local chain (Anvil)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    
    # 5. Wait for the receipt
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    if receipt.status == 1:
        print(f"✅ SUCCESS: Bounty #{bounty_id} claimed!")
        print(f"🔗 TX Hash: {tx_hash.hex()}")
    else:
        print(f"❌ FAILED: Transaction reverted.")
