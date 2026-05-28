import pytest
import base64
import hashlib
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes, serialization
from runtime.crypto import encrypt_data, decrypt_data, hash_email, get_public_key_pem, decrypt_api_key

def test_db_encryption():
    plain = "sensitive_data_123"
    cipher = encrypt_data(plain)
    assert cipher != plain
    
    decrypted = decrypt_data(cipher)
    assert decrypted == plain

def test_email_hashing():
    email = "Test.User@Example.Com "
    h1 = hash_email(email)
    h2 = hash_email("test.user@example.com")
    assert h1 == h2
    expected = hashlib.sha256(b"test.user@example.com").hexdigest()
    assert h1 == expected

def test_rsa_transit_encryption_decryption():
    # 1. Get server public key PEM
    pub_pem = get_public_key_pem()
    assert "-----BEGIN PUBLIC KEY-----" in pub_pem
    
    # 2. Load public key to encrypt
    public_key = serialization.load_pem_public_key(pub_pem.encode("utf-8"))
    
    secret_key = "my-super-secret-gemini-key-123"
    
    # Encrypt using RSA-OAEP with SHA-256 (exactly like Web Crypto client)
    ciphertext = public_key.encrypt(
        secret_key.encode("utf-8"),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    
    enc_base64 = base64.b64encode(ciphertext).decode("utf-8")
    
    # 3. Decrypt using server private key
    decrypted = decrypt_api_key(enc_base64)
    assert decrypted == secret_key
