import pytest
import base64
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app
from runtime.crypto import get_public_key_pem
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes, serialization

client = TestClient(app)

@pytest.fixture(autouse=True)
def mock_similarity_and_perplexity():
    """Mocks similarity and perplexity evaluations at their source to avoid network calls."""
    with patch("analysis.evaluator.calculate_similarity", return_value=0.8), \
         patch("app.humanizer.judge.calculate_similarity", return_value=0.8), \
         patch("analysis.evaluator.calculate_perplexity", return_value={"perplexity": 12.5, "fallback": False}), \
         patch("runtime.registry.ModelRegistry.get_embedding_model", return_value=None), \
         patch("runtime.registry.ModelRegistry.get_perplexity_model", return_value=None):
        yield

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_get_public_key():
    response = client.get("/api/auth/public-key")
    assert response.status_code == 200
    assert "public_key" in response.json()
    assert "-----BEGIN PUBLIC KEY-----" in response.json()["public_key"]

def test_signup_login_integration():
    email = "integration_test_user@example.com"
    password = "password123"
    full_name = "Integration Test User"
    
    # 1. Signup
    signup_payload = {
        "email": email,
        "password": password,
        "full_name": full_name
    }
    
    # Let's perform signup
    signup_res = client.post("/api/auth/signup", json=signup_payload)
    if signup_res.status_code == 400 and "already exists" in signup_res.json()["detail"]:
        pass
    else:
        assert signup_res.status_code == 200
        assert "access_token" in signup_res.json()
        assert signup_res.json()["user"]["email"] == email
        
    # 2. Login
    login_payload = {
        "email": email,
        "password": password
    }
    login_res = client.post("/api/auth/login", json=login_payload)
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()
    assert login_res.json()["user"]["full_name"] == full_name
    
    # 3. Retrieve user profile (Me)
    token = login_res.json()["access_token"]
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == email

def test_transit_key_decryption_on_rewrite():
    # 1. Fetch public key
    pub_res = client.get("/api/auth/public-key")
    pub_pem = pub_res.json()["public_key"]
    
    # 2. Encrypt mock Gemini API key using public key
    public_key = serialization.load_pem_public_key(pub_pem.encode("utf-8"))
    mock_api_key = "AIzaSyFakeKeyForIntegrationTesting"
    ciphertext = public_key.encrypt(
        mock_api_key.encode("utf-8"),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    enc_base64 = base64.b64encode(ciphertext).decode("utf-8")
    
    payload = {
        "original_text": "optimise this colour scheme 🎨",
        "tone": "professional"
    }
    
    # Patch MODEL_MODE to "gemini_byok" to force routing to the BYOK pipeline
    with patch("analysis.rewriter.MODEL_MODE", "gemini_byok"):
        rewrite_res = client.post(
            "/api/ppt/rewrite",
            json=payload,
            headers={"X-Gemini-API-Key": enc_base64}
        )
        assert rewrite_res.status_code == 200
        # Cleaned text should be normalized via editorial rules
        assert rewrite_res.json()["final_text"] == "Optimize this color scheme."
