import secrets

# Generates a 32-character (16-byte) random hex string
new_salt = secrets.token_hex(16)
print(f"Your COMMITMENT_SALT: {new_salt}")