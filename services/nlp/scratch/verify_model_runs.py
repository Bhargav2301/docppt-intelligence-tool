import requests
import sqlite3
import os

BASE_URL = "http://localhost:8000/api"
DB_PATH = "services/nlp/docppt.db"

def get_latest_model_run():
    if not os.path.exists(DB_PATH):
        # try relative path if run from scratch/
        alt_path = "docppt.db"
        if os.path.exists(alt_path):
            conn = sqlite3.connect(alt_path)
        else:
            return None
    else:
        conn = sqlite3.connect(DB_PATH)
    
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, run_type, model_name, model_mode, duration_ms, status, error_code, error_message 
        FROM model_runs 
        ORDER BY created_at DESC 
        LIMIT 1
    """)
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def verify_all_modes():
    print("=== Starting LLM Mode and ModelRun Verification ===")
    
    # 1. Login as developer to set setting context (since settings updates default to developer user settings)
    dev_login_payload = {
        "email": "local_user@example.com",
        "password": "password"
    }
    res = requests.post(f"{BASE_URL}/auth/login", json=dev_login_payload)
    if res.status_code != 200:
        print(f"Failed to log in as developer: {res.text}")
        return
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("Logged in successfully. Token obtained.")

    modes = [
        {
            "name": "Local CPU",
            "payload": {
                "model_mode": "local_cpu",
                "ppt_sensitivity": "balanced",
                "theme": "dark"
            }
        },
        {
            "name": "Local GPU",
            "payload": {
                "model_mode": "local_gpu",
                "ppt_sensitivity": "balanced",
                "theme": "dark"
            }
        },
        {
            "name": "Extractive-only",
            "payload": {
                "model_mode": "extractive_only",
                "ppt_sensitivity": "balanced",
                "theme": "dark"
            }
        },
        {
            "name": "Managed Hosted LLM (Fallback expected)",
            "payload": {
                "model_mode": "managed_endpoint",
                "ppt_sensitivity": "balanced",
                "theme": "dark",
                "advanced_instruction_model": "placeholder-model",
                "advanced_model_endpoint": "https://api.managed-llm.com/v1"
            }
        },
        {
            "name": "Custom Local/OpenAI Endpoint (Fallback expected)",
            "payload": {
                "model_mode": "user_hosted_endpoint",
                "ppt_sensitivity": "balanced",
                "theme": "dark",
                "advanced_instruction_model": "custom-ollama-model",
                "advanced_model_endpoint": "http://localhost:11434/v1" # assumed offline/unreachable
            }
        }
    ]

    results = []

    for mode in modes:
        print(f"\n--- Testing Mode: {mode['name']} ---")
        # Update settings
        put_res = requests.put(f"{BASE_URL}/settings", headers=headers, json=mode["payload"])
        if put_res.status_code != 200:
            print(f"Failed to update settings for {mode['name']}: {put_res.text}")
            continue
        
        # Trigger rewrite
        rewrite_payload = {
            "original_text": "Tasky is a mobile app for tracking task deadlines.",
            "tone": "professional"
        }
        post_res = requests.post(f"{BASE_URL}/ppt/rewrite", headers=headers, json=rewrite_payload)
        print(f"Rewrite status: {post_res.status_code}")
        
        # Query database for the latest ModelRun row
        latest_run = get_latest_model_run()
        results.append({
            "mode_name": mode["name"],
            "model_mode": mode["payload"]["model_mode"],
            "latest_run": latest_run,
            "rewrite_response": post_res.json() if post_res.status_code == 200 else None
        })

    # Display clean report
    print("\n================ MODEL RUN VERIFICATION SUMMARY ================")
    for r in results:
        print(f"\nMode: {r['mode_name']} (Configured: {r['model_mode']})")
        if r['model_mode'] == 'extractive_only':
            print("  Note: Extractive-only bypasses generation. No ModelRun expected.")
            print(f"  Response: {r['rewrite_response']}")
        else:
            run = r['latest_run']
            if run:
                print(f"  ModelRun ID: {run['id']}")
                print(f"  Model Used:  {run['model_name']}")
                print(f"  Model Mode:  {run['model_mode']}")
                print(f"  Duration:    {run['duration_ms']} ms")
                print(f"  Status:      {run['status']}")
                print(f"  Error Code:  {run['error_code']}")
                print(f"  Error Msg:   {run['error_message']}")
            else:
                print("  WARNING: No ModelRun entry found in DB!")
            print(f"  Response: {r['rewrite_response']}")

if __name__ == "__main__":
    verify_all_modes()
