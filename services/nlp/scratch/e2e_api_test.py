import requests
import json
import time

BASE_URL = "http://localhost:8000/api"

def run_tests():
    print("=== Starting E2E API Verification ===")
    
    # 1. Sign Up validation - Too short password
    print("\n--- Test 1: Signup password validation (< 8 chars) ---")
    bad_signup_payload = {
        "email": "test_weak@example.com",
        "password": "123",
        "full_name": "Weak User"
    }
    res = requests.post(f"{BASE_URL}/auth/signup", json=bad_signup_payload)
    print(f"Status Code: {res.status_code}")
    print(f"Response: {res.text}")
    assert res.status_code == 400, "Should reject passwords shorter than 8 characters"
    assert "at least 8 characters" in res.json().get("detail", ""), "Should return validation error message"
    print("Success: Rejected weak password correctly.")

    # 2. Sign Up success
    print("\n--- Test 2: Successful Signup ---")
    random_email = f"user_{int(time.time())}@example.com"
    good_signup_payload = {
        "email": random_email,
        "password": "password123",
        "full_name": "Valid User"
    }
    res = requests.post(f"{BASE_URL}/auth/signup", json=good_signup_payload)
    print(f"Status Code: {res.status_code}")
    assert res.status_code == 200, "Signup should succeed"
    user_data = res.json()
    token = user_data["access_token"]
    print(f"Success: Registered user {random_email}. Token: {token[:10]}...")

    headers = {"Authorization": f"Bearer {token}"}

    # 3. Get Me Profile
    print("\n--- Test 3: Get current user profile ---")
    res = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    print(f"Status Code: {res.status_code}")
    assert res.status_code == 200
    profile = res.json()
    assert profile["email"] == random_email
    assert profile["role"] == "user"
    print(f"Success: Profile matches registered email and defaults to 'user' role.")

    # 4. Settings Retrieval and Updates
    print("\n--- Test 4: Get and update User Settings ---")
    res = requests.get(f"{BASE_URL}/settings", headers=headers)
    assert res.status_code == 200
    settings = res.json()
    print(f"Current model_mode: {settings.get('model_mode')}")

    # Update settings to user_hosted_endpoint
    update_payload = {
        "model_mode": "user_hosted_endpoint",
        "ppt_sensitivity": "balanced",
        "theme": "dark",
        "retain_source_files": True,
        "advanced_instruction_model": "mistral-7b",
        "advanced_model_endpoint": "http://localhost:11434/v1"
    }
    res = requests.put(f"{BASE_URL}/settings", headers=headers, json=update_payload)
    assert res.status_code == 200
    updated_settings = res.json()
    assert updated_settings["model_mode"] == "user_hosted_endpoint"
    assert updated_settings["advanced_instruction_model"] == "mistral-7b"
    assert updated_settings["advanced_model_endpoint"] == "http://localhost:11434/v1"
    print("Success: settings updated to user_hosted_endpoint successfully.")

    # 5. Developer Dashboard Protection
    print("\n--- Test 5: Verify Developer Panel is blocked for normal users ---")
    res = requests.get(f"{BASE_URL}/telemetry/events", headers=headers)
    print(f"Status Code: {res.status_code}")
    print(f"Response: {res.text}")
    assert res.status_code == 403, "Should return 403 Forbidden for role 'user'"
    print("Success: Dev-only telemetry endpoint is blocked for standard users.")

    # 6. Seeded Developer Account Login
    print("\n--- Test 6: Log in as seeded Developer user ---")
    dev_login_payload = {
        "email": "local_user@example.com",
        "password": "password"
    }
    res = requests.post(f"{BASE_URL}/auth/login", json=dev_login_payload)
    print(f"Status Code: {res.status_code}")
    assert res.status_code == 200
    dev_data = res.json()
    dev_token = dev_data["access_token"]
    dev_headers = {"Authorization": f"Bearer {dev_token}"}
    
    # Check profile of dev user
    res = requests.get(f"{BASE_URL}/auth/me", headers=dev_headers)
    dev_profile = res.json()
    assert dev_profile["role"] == "developer", "Seeded user should have 'developer' role"
    print("Success: Logged in as developer user successfully.")

    # 7. Access Telemetry Events as Developer
    print("\n--- Test 7: Fetch Telemetry logs as Developer ---")
    res = requests.get(f"{BASE_URL}/telemetry/events", headers=dev_headers)
    print(f"Status Code: {res.status_code}")
    assert res.status_code == 200
    events_data = res.json()
    print(f"Total telemetry logs: {events_data.get('total')}")
    print("Success: Developer successfully fetched telemetries.")

    # 8. Record Telemetry Crash Event (Consent compliant)
    print("\n--- Test 8: Record telemetry crash event ---")
    crash_payload = {
        "route": "/process/doc",
        "error_type": "TypeError",
        "message": "C:\\Users\\dev_user\\documents\\secret.txt failed to open",
        "stack_summary": "Traceback (most recent call):\n  File \"C:\\Users\\dev_user\\app.py\", line 10, in run\n    raise TypeError(\"Failed\")",
        "consent_flag": True
    }
    res = requests.post(f"{BASE_URL}/telemetry/crash", headers=headers, json=crash_payload)
    assert res.status_code == 200
    print("Success: Telemetry crash log successfully saved.")

    # Verify PII was redacted and message/stack was saved correctly in the db
    print("\n--- Test 9: Verify PII Redaction on Telemetry logs ---")
    res = requests.get(f"{BASE_URL}/telemetry/events", headers=dev_headers)
    events = res.json()["events"]
    # Find our logged TypeError
    logged_event = next((e for e in events if e["error_type"] == "TypeError"), None)
    assert logged_event is not None, "Log should be in the DB"
    print(f"Original Msg:  {crash_payload['message']}")
    print(f"Redacted Msg:  {logged_event['message']}")
    print(f"Original Stack: {crash_payload['stack_summary']}")
    print(f"Redacted Stack: {logged_event['stack_summary']}")
    assert "C:\\Users\\<user>" in logged_event["message"], "System paths must be scrubbed of usernames"
    assert "C:\\Users\\<user>" in logged_event["stack_summary"], "Stack trace paths must be scrubbed of usernames"
    print("Success: PII paths scrubbed successfully.")

    print("\n=== All E2E API Verification Scenarios PASSED ===")

if __name__ == "__main__":
    run_tests()
