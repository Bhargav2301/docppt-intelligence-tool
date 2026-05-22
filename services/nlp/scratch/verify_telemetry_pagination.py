import requests

BASE_URL = "http://localhost:8000/api"

def verify_telemetry_pagination():
    print("=== Starting Telemetry Pagination & Cap Verification ===")
    
    # 1. Developer login
    dev_login_payload = {
        "email": "local_user@example.com",
        "password": "password"
    }
    res = requests.post(f"{BASE_URL}/auth/login", json=dev_login_payload)
    if res.status_code != 200:
        print(f"Failed to log in as developer: {res.text}")
        return
    dev_token = res.json()["access_token"]
    dev_headers = {"Authorization": f"Bearer {dev_token}"}
    
    # Get initial count
    get_res = requests.get(f"{BASE_URL}/telemetry/events?limit=1", headers=dev_headers)
    initial_total = get_res.json().get("total", 0)
    print(f"Initial crash logs in DB: {initial_total}")
    
    # Log 15 new crashes (to verify pagination limit/capping without creating too many rows)
    # We will query with limit=5 and verify we get exactly 5, and page 2 gives correct offset.
    print("Logging 15 simulated crash events...")
    for i in range(15):
        crash_payload = {
            "route": f"/test/route/{i}",
            "error_type": "ValueError",
            "message": f"Simulated error {i} with user directory C:\\Users\\bharg\\temp",
            "stack_summary": f"Traceback for error {i}\n  File C:\\Users\\bharg\\app.py, line {i}",
            "consent_flag": True
        }
        post_res = requests.post(f"{BASE_URL}/telemetry/crash", headers=dev_headers, json=crash_payload)
        if post_res.status_code != 200:
            print(f"Failed to log crash {i}: {post_res.text}")
            return

    # Fetch with limit=5, page=1
    res_p1 = requests.get(f"{BASE_URL}/telemetry/events?page=1&limit=5", headers=dev_headers)
    assert res_p1.status_code == 200
    p1_data = res_p1.json()
    assert len(p1_data["events"]) == 5
    assert p1_data["total"] >= 15
    print("Page 1 with limit=5 returns exactly 5 events.")

    # Fetch with limit=5, page=2
    res_p2 = requests.get(f"{BASE_URL}/telemetry/events?page=2&limit=5", headers=dev_headers)
    assert res_p2.status_code == 200
    p2_data = res_p2.json()
    assert len(p2_data["events"]) == 5
    # Verify that the events in page 2 are different from page 1
    p1_ids = {e["id"] for e in p1_data["events"]}
    p2_ids = {e["id"] for e in p2_data["events"]}
    assert p1_ids.isdisjoint(p2_ids), "Page 1 and Page 2 events should be mutually exclusive"
    print("Page 2 with limit=5 returns 5 exclusive events. Pagination works!")

    # Verify limit capping (request limit=150, should be capped at 100)
    res_capped = requests.get(f"{BASE_URL}/telemetry/events?limit=150", headers=dev_headers)
    assert res_capped.status_code == 200
    capped_data = res_capped.json()
    assert capped_data["limit"] == 100, "Limit should be capped at 100"
    print("Request for limit=150 was successfully capped to 100. Capping works!")

    # Verify consent settings override
    print("Testing consent settings override...")
    # Send a crash with consent_flag=False
    declined_payload = {
        "route": "/test/declined",
        "error_type": "AuthError",
        "message": "Should not be saved",
        "stack_summary": "Should not be saved",
        "consent_flag": False
    }
    declined_res = requests.post(f"{BASE_URL}/telemetry/crash", headers=dev_headers, json=declined_payload)
    assert declined_res.status_code == 200
    assert "declined by user. Wiped." in declined_res.json().get("detail", "")
    print("decline payload correctly wiped and ignored.")

    print("\n=== Telemetry Pagination & Consent Verification PASSED ===")

if __name__ == "__main__":
    verify_telemetry_pagination()
