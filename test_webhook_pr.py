#!/usr/bin/env python
"""Test script to simulate a PR webhook event and verify logging."""

import json
import hmac
import hashlib
import requests
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from automation_agent.config import Config

def create_test_pr_payload():
    """Create a test PR webhook payload."""
    return {
        "action": "synchronize",
        "number": 123,
        "pull_request": {
            "id": 123456789,
            "number": 123,
            "title": "Test PR for debugging webhook flow",
            "state": "open",
            "head": {
                "ref": "test-branch",
                "sha": "abc123def456789012345678901234567890abcd"
            },
            "base": {
                "ref": "main",
                "sha": "def456abc789012345678901234567890abcdef1"
            },
            "user": {
                "login": "test-user"
            }
        }
    }

def send_webhook(url: str, secret: str, payload: dict, event_type: str = "pull_request"):
    """Send a webhook request with proper signature."""
    body = json.dumps(payload).encode('utf-8')
    
    # Create HMAC signature
    mac = hmac.new(secret.encode(), msg=body, digestmod=hashlib.sha256)
    signature = f"sha256={mac.hexdigest()}"
    
    headers = {
        "X-GitHub-Event": event_type,
        "X-Hub-Signature-256": signature,
        "X-GitHub-Delivery": "test-delivery-12345",
        "Content-Type": "application/json"
    }
    
    print(f"\n{'='*60}")
    print(f"Sending {event_type} webhook to {url}")
    print(f"{'='*60}")
    print(f"Event: {event_type}")
    print(f"Action: {payload.get('action', 'N/A')}")
    print(f"PR Number: {payload.get('number', 'N/A')}")
    print(f"Signature: {signature[:20]}...")
    print(f"{'='*60}\n")
    
    try:
        response = requests.post(url, data=body, headers=headers, timeout=10)
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.json()}")
        return response
    except Exception as e:
        print(f"Error: {e}")
        return None

def check_session_memory():
    """Check the session memory file for recent runs."""
    memory_file = "session_memory.json"
    if os.path.exists(memory_file):
        print(f"\n{'='*60}")
        print("Session Memory Contents")
        print(f"{'='*60}")
        with open(memory_file, 'r') as f:
            data = json.load(f)
            runs = data.get('runs', [])
            print(f"Total runs: {len(runs)}")
            if runs:
                print("\nMost recent runs:")
                for run in runs[:3]:
                    print(f"  - Run ID: {run.get('id')}")
                    print(f"    Trigger: {run.get('trigger_type')}")
                    print(f"    Run Type: {run.get('run_type')}")
                    print(f"    PR: #{run.get('pr_number', 'N/A')}")
                    print(f"    Status: {run.get('status')}")
                    print(f"    Skip Reason: {run.get('skip_reason', 'N/A')}")
                    print()
    else:
        print(f"\n⚠️  Session memory file not found: {memory_file}")

if __name__ == "__main__":
    # Load config
    config = Config()
    
    # Check if server is configured
    if not config.GITHUB_WEBHOOK_SECRET:
        print("❌ GITHUB_WEBHOOK_SECRET not set in .env")
        sys.exit(1)
    
    # Webhook URL (default to localhost)
    webhook_url = os.getenv("WEBHOOK_URL", "http://localhost:8080/webhook")
    
    print(f"Testing PR webhook flow...")
    print(f"Webhook URL: {webhook_url}")
    print(f"Repository: {config.get_repo_full_name()}")
    print(f"Trigger Mode: {config.TRIGGER_MODE}")
    print(f"PR Trigger Enabled: {config.ENABLE_PR_TRIGGER}")
    
    # Create and send test payload
    payload = create_test_pr_payload()
    response = send_webhook(webhook_url, config.GITHUB_WEBHOOK_SECRET, payload)
    
    if response and response.status_code == 200:
        print("\n✅ Webhook accepted successfully!")
        print("\nWaiting 3 seconds for processing...")
        import time
        time.sleep(3)
        
        # Check session memory
        check_session_memory()
    else:
        print("\n❌ Webhook failed!")
        if response:
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
