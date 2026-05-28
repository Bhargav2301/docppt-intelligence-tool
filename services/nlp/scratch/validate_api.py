import requests
import base64
import json
import os
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes, serialization

API_URL = "http://localhost:8000"

def run_validation():
    print("1. Testing Health Check...")
    r = requests.get(f"{API_URL}/health")
    assert r.status_code == 200, f"Health check failed: {r.text}"
    print("Health Check: OK")

    print("\n2. Seeding / Logging In Developer User...")
    # Seeding should have created local_user@example.com
    login_payload = {
        "email": "local_user@example.com",
        "password": "password"
    }
    r = requests.post(f"{API_URL}/api/auth/login", json=login_payload)
    assert r.status_code == 200, f"Login failed: {r.text}"
    auth_data = r.json()
    token = auth_data["access_token"]
    user_info = auth_data["user"]
    print(f"Login: OK. Authenticated as: {user_info['full_name']} (Role: {user_info['role']})")

    print("\n3. Testing Public Key Retrieval...")
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{API_URL}/api/auth/public-key", headers=headers)
    assert r.status_code == 200, f"Public key retrieval failed: {r.text}"
    pub_key_pem = r.json()["public_key"]
    assert "-----BEGIN PUBLIC KEY-----" in pub_key_pem
    print("Public Key Retrieval: OK")

    print("\n4. Encrypting Mock API Key...")
    # Load public key
    public_key = serialization.load_pem_public_key(pub_key_pem.encode("utf-8"))
    mock_api_key = "AIzaSyFakeKeyForLiveTesting"
    ciphertext = public_key.encrypt(
        mock_api_key.encode("utf-8"),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    enc_key_b64 = base64.b64encode(ciphertext).decode("utf-8")
    print("Encryption: OK")

    print("\n5. Testing /rewrite endpoint with Encrypted Gemini API Key...")
    rewrite_payload = {
        "original_text": "we want to optimise this colour scheme.",
        "tone": "professional"
    }
    headers["X-Gemini-API-Key"] = enc_key_b64
    r = requests.post(f"{API_URL}/api/ppt/rewrite", json=rewrite_payload, headers=headers)
    assert r.status_code == 200, f"Rewrite failed: {r.text}"
    rewritten_text = r.json()["final_text"]
    print(f"Original: {rewrite_payload['original_text']}")
    print(f"Rewritten: {rewritten_text}")
    assert "optimize" in rewritten_text.lower()
    assert "color" in rewritten_text.lower()
    print("Rewrite Endpoint: OK (All editorial rules applied!)")

    print("\n6. Testing /process endpoint with PPT upload...")
    ppt_path = "sample_presentation.pptx"
    if not os.path.exists(ppt_path):
        ppt_path = "../sample_presentation.pptx"
    
    with open(ppt_path, "rb") as f:
        files = {"file": (os.path.basename(ppt_path), f, "application/vnd.openxmlformats-officedocument.presentationml.presentation")}
        r = requests.post(f"{API_URL}/api/ppt/process", files=files, headers=headers)
    
    assert r.status_code == 200, f"PPT processing failed: {r.text}"
    process_data = r.json()
    session_id = process_data["session"]["id"]
    print(f"PPT Processing: OK. Session ID: {session_id}")
    print(f"Total Slides: {process_data['data']['total_slides']}")
    
    print("\n7. Compiling Session...")
    # Create simple modifications matching the schema
    modifications = []
    for slide in process_data["data"]["slides"]:
        for segment in slide["segments"]:
            modifications.append({
                "slide_index": segment["slide_index"],
                "shape_id": segment["shape_id"],
                "paragraph_index": segment["paragraph_index"],
                "run_index": segment["run_index"],
                "new_text": segment["original_text"] + " (Processed)"
            })
            
    compile_payload = {"modifications": json.dumps(modifications)}
    r = requests.post(f"{API_URL}/api/ppt/compile_session/{session_id}", data=compile_payload, headers=headers)
    assert r.status_code == 200, f"Compilation failed: {r.text}"
    
    out_ppt_path = "compiled_output.pptx"
    with open(out_ppt_path, "wb") as f:
        f.write(r.content)
    
    print(f"Compilation: OK. Saved to {out_ppt_path} ({os.path.getsize(out_ppt_path)} bytes)")
    print("\nAPI Integration Validation: ALL PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_validation()
