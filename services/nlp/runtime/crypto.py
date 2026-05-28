import os
import base64
import hashlib
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.fernet import Fernet

# File paths for persisted keys (for local development continuity)
CRYPTO_DIR = os.path.dirname(os.path.abspath(__file__))
PRIVATE_KEY_PATH = os.path.join(CRYPTO_DIR, "private_key.pem")
DB_KEY_PATH = os.path.join(CRYPTO_DIR, "db_key.key")

# In-memory caches
_private_key = None
_public_key_pem = None
_db_fernet = None

def init_keys():
    """
    Initializes RSA keypair and Fernet DB keys.
    Generates new files if they don't exist, otherwise loads them.
    """
    global _private_key, _public_key_pem, _db_fernet
    
    # 1. RSA Transit Keys
    if os.path.exists(PRIVATE_KEY_PATH):
        try:
            with open(PRIVATE_KEY_PATH, "rb") as key_file:
                _private_key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=None
                )
        except Exception as e:
            print(f"Error loading private key: {e}. Re-generating.")
            _private_key = None
            
    if _private_key is None:
        _private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        try:
            pem = _private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            )
            with open(PRIVATE_KEY_PATH, "wb") as key_file:
                key_file.write(pem)
        except Exception as e:
            print(f"Failed to persist private key: {e}")

    # Derive public key PEM
    public_key = _private_key.public_key()
    _public_key_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode("utf-8")

    # 2. Fernet Database Key
    db_key = os.getenv("DATABASE_ENCRYPTION_KEY")
    if not db_key:
        if os.path.exists(DB_KEY_PATH):
            try:
                with open(DB_KEY_PATH, "rb") as f:
                    db_key = f.read().decode("utf-8").strip()
            except Exception as e:
                print(f"Error loading DB key: {e}")
                
        if not db_key:
            db_key = Fernet.generate_key().decode("utf-8")
            try:
                with open(DB_KEY_PATH, "wb") as f:
                    f.write(db_key.encode("utf-8"))
            except Exception as e:
                print(f"Failed to persist DB key: {e}")
                
    _db_fernet = Fernet(db_key.encode("utf-8"))

# Run initialization at module load
init_keys()

def get_public_key_pem() -> str:
    """Returns the RSA public key in PEM format."""
    return _public_key_pem

def decrypt_api_key(encrypted_base64: str) -> str:
    """
    Decrypts a base64-encoded ciphertext using the server's RSA private key (RSA-OAEP + SHA-256).
    """
    if not encrypted_base64:
        return ""
    try:
        ciphertext = base64.b64decode(encrypted_base64)
        decrypted = _private_key.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return decrypted.decode("utf-8")
    except Exception as e:
        raise ValueError(f"Decryption failed: {e}")

def encrypt_data(plain_text: str) -> str:
    """Symmetrically encrypts plaintext using Fernet (AES-GCM/CBC)."""
    if plain_text is None:
        return None
    token = _db_fernet.encrypt(plain_text.encode("utf-8"))
    return token.decode("utf-8")

def decrypt_data(cipher_text: str) -> str:
    """Symmetrically decrypts Fernet ciphertext."""
    if cipher_text is None:
        return None
    decrypted = _db_fernet.decrypt(cipher_text.encode("utf-8"))
    return decrypted.decode("utf-8")

def hash_email(email: str) -> str:
    """
    Generates a deterministic SHA-256 hash of a lowercase email.
    Acts as a blind index for lookups in the encrypted user DB.
    """
    if email is None:
        return None
    cleaned = email.lower().strip()
    return hashlib.sha256(cleaned.encode("utf-8")).hexdigest()
