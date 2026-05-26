import sys
import os

# Add services/nlp to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from auth_utils import hash_password, verify_password
from analysis.artifact_detector import detect_artifacts

def test_password_hashing():
    print("Testing password hashing...")
    # Test new hashing format
    pwd = "MySecretPassword123"
    hashed = hash_password(pwd)
    print(f"Hashed (new format): {hashed}")
    assert verify_password(hashed, pwd) is True
    assert verify_password(hashed, "wrong_password") is False

    # Test legacy hashing verification
    # Old hash was: secrets.token_hex(16) -> pbkdf2_hmac with utf-8 encoded hex string salt
    import hashlib
    import secrets
    legacy_salt = secrets.token_hex(16)
    legacy_key = hashlib.pbkdf2_hmac(
        'sha256',
        pwd.encode('utf-8'),
        legacy_salt.encode('utf-8'),
        100000
    )
    legacy_hashed = f"{legacy_salt}:{legacy_key.hex()}"
    print(f"Legacy Hashed: {legacy_hashed}")
    assert verify_password(legacy_hashed, pwd) is True
    assert verify_password(legacy_hashed, "wrong_password") is False
    print("Password hashing tests PASSED!")

def test_classifier_improvements():
    print("\nTesting classifier improvements...")
    
    # 1. Math operator test: should NOT be flagged
    text1 = "Profit is <3% this quarter."
    flags1 = detect_artifacts(text1)
    print(f"Flags for '{text1}': {flags1}")
    assert len(flags1) == 0, f"Math operator '<3%' incorrectly flagged: {flags1}"
    
    # 2. Simple domain test: should NOT be flagged
    text2 = "Visit www.absolinsoft.com for info."
    flags2 = detect_artifacts(text2)
    print(f"Flags for '{text2}': {flags2}")
    assert len(flags2) == 0, f"Simple domain link incorrectly flagged: {flags2}"

    # 3. Bare URL test: SHOULD be flagged
    text3 = "Here is the raw link http://docs.google.com/document/d/12345/edit to view."
    flags3 = detect_artifacts(text3)
    print(f"Flags for '{text3}': {flags3}")
    assert len(flags3) > 0, "Bare URL was not flagged!"
    assert any(f['type'] == 'url_artifact' for f in flags3)

    # 4. Placeholder text test: SHOULD be flagged
    text4 = "Replace these with your real anonymized customer outcomes [insert metric here]"
    flags4 = detect_artifacts(text4)
    print(f"Flags for '{text4}': {flags4}")
    assert len(flags4) > 0, "Placeholder text was not flagged!"
    assert any(f['type'] == 'placeholder_text' for f in flags4)
    
    print("Classifier improvements tests PASSED!")

if __name__ == "__main__":
    try:
        test_password_hashing()
        test_classifier_improvements()
        print("\nALL BACKEND VERIFICATIONS PASSED SUCCESSFULLY!")
    except AssertionError as e:
        print(f"\nVERIFICATION FAILED: {e}")
        sys.exit(1)
