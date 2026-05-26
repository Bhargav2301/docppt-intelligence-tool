import hashlib
import secrets

def hash_password(password: str) -> str:
    """
    Hashes a password using PBKDF2-HMAC-SHA256 with 100,000 iterations and a 16-byte salt.
    Returns a string in the format salt_hex:key_hex.
    """
    salt = secrets.token_bytes(16)
    key = hashlib.pbkdf2_hmac(
        'sha256', 
        password.encode('utf-8'), 
        salt, 
        100000
    )
    return f"{salt.hex()}:{key.hex()}"

def verify_password(stored_password: str, provided_password: str) -> bool:
    """
    Verifies a password against its stored hash, supporting both raw byte salts (new)
    and hex-encoded string salts (legacy).
    """
    if not stored_password or ":" not in stored_password:
        return False
    try:
        salt_hex, key_hex = stored_password.split(":")
        
        # 1. New Format: Salt is a hex representation of raw bytes.
        try:
            salt_bytes = bytes.fromhex(salt_hex)
            key_new = hashlib.pbkdf2_hmac(
                'sha256', 
                provided_password.encode('utf-8'), 
                salt_bytes, 
                100000
            )
            if secrets.compare_digest(key_new.hex(), key_hex):
                return True
        except ValueError:
            pass
            
        # 2. Legacy Format: Salt is a hex string encoded as utf-8.
        key_legacy = hashlib.pbkdf2_hmac(
            'sha256', 
            provided_password.encode('utf-8'), 
            salt_hex.encode('utf-8'), 
            100000
        )
        return secrets.compare_digest(key_legacy.hex(), key_hex)
    except Exception:
        return False
