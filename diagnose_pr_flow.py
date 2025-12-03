#!/usr/bin/env python
"""Comprehensive diagnostic script for PR webhook flow."""

import json
import hmac
import hashlib
import requests
import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from automation_agent.config import Config

def print_section(title):
    """Print a section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")

def check_configuration():
    """Check and display current configuration."""
    print_section("Configuration Check")
    config = Config()
    
    print(f"Repository: {config.get_repo_full_name()}")
    print(f"LLM Provider: {config.LLM_PROVIDER}")
    print(f"Review Provider: {config.REVIEW_PROVIDER}")
    print()
    print("PR-Centric Configuration:")
    print(f"  TRIGGER_MODE: {config.TRIGGER_MODE}")
    print(f"  ENABLE_PR_TRIGGER: {config.ENABLE_PR_TRIGGER}")
    print(f"  ENABLE_PUSH_TRIGGER: {config.ENABLE_PUSH_TRIGGER}")
    print(f"  POST_REVIEW_ON_PR: {config.POST_REVIEW_ON_PR}")
    print(f"  GROUP_AUTOMATION_UPDATES: {config.GROUP_AUTOMATION_UPDATES}")
    print()
    print("Trivial Change Filter:")
    print(f"  TRIVIAL_CHANGE_FILTER_ENABLED: {config.TRIVIAL_CHANGE_FILTER_ENABLED}")
    print(f"  TRIVIAL_MAX_LINES: {config.TRIVIAL_MAX_LINES}")
    
    # Validate required settings
    errors = []
    if not config.GITHUB_TOKEN:
        errors.append("GITHUB_TOKEN not set")
    if not config.GITHUB_WEBHOOK_SECRET:
        errors.append("GITHUB_WEBHOOK_SECRET not set")
    
    if errors:
        print("\n❌ Configuration Errors:")
        for error in errors:
            print(f"   - {error}")
        return False
    else:
        print("\n✅ Configuration is valid")
        return True

def check_server_health(url="http://localhost:8080"):
    """Check if server is responding."""
    print_section("Server Health Check")
    try:
        response = requests.get(f"{url}/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Server is running at {url}")
            print(f"   Status: {data.get('status')}")
            print(f"   Uptime: {data.get('uptime')}")
            return True
        else:
            print(f"❌ Server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to server at {url}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def create_pr_payload(action="synchronize", pr_number=999):
    """Create a test PR webhook payload."""
    return {
        "action": action,
        "number": pr_number,
        "pull_request": {
            "id": 123456789,
            "number": pr_number,
            "title": f"[TEST] PR for debugging webhook flow ({action})",
            "state": "open",
            "head": {
                "ref": "test-debug-branch",
                "sha": "abc123def456789012345678901234567890abcd"
            },
            "base": {
                "ref": "main",
                "sha": "def456abc789012345678901234567890abcdef1"
            },
            "user": {
                "login": "test-user"
            },
            "html_url": f"https://github.com/test/repo/pull/{pr_number}"
        }
    }

def send_webhook(url, secret, payload, event_type="pull_request"):
    """Send a webhook request with proper signature."""
    body = json.dumps(payload).encode('utf-8')
    
    # Create HMAC signature
    mac = hmac.new(secret.encode(), msg=body, digestmod=hashlib.sha256)
    signature = f"sha256={mac.hexdigest()}"
    
    headers = {
        "X-GitHub-Event": event_type,
        "X-Hub-Signature-256": signature,
        "X-GitHub-Delivery": f"test-delivery-{int(time.time())}",
        "Content-Type": "application/json"
    }
    
    print_section(f"Sending {event_type.upper()} Webhook")
    print(f"URL: {url}")
    print(f"Event Type: {event_type}")
    if event_type == "pull_request":
        print(f"Action: {payload.get('action')}")
        print(f"PR Number: #{payload.get('number')}")
        pr_data = payload.get('pull_request', {})
        print(f"PR Title: {pr_data.get('title', 'N/A')}")
        print(f"Head: {pr_data.get('head', {}).get('ref')}@{pr_data.get('head', {}).get('sha', '')[:7]}")
        print(f"Base: {pr_data.get('base', {}).get('ref')}")
    
    try:
        print("\nSending request...")
        response = requests.post(url, data=body, headers=headers, timeout=10)
        print(f"\n✅ Response received:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"\n❌ Error sending webhook: {e}")
        return False

def check_session_memory():
    """Check the session memory file for recent runs."""
    print_section("Session Memory Check")
    memory_file = "session_memory.json"
    
    if not os.path.exists(memory_file):
        print(f"⚠️  Session memory file not found: {memory_file}")
        print("   This is normal if no automation has run yet.")
        return
    
    with open(memory_file, 'r') as f:
        data = json.load(f)
        runs = data.get('runs', [])
        metrics = data.get('metrics', {})
    
    print(f"Total runs in history: {len(runs)}")
    print(f"Total tokens used: {metrics.get('total_tokens', 0)}")
    print(f"Total cost: ${metrics.get('total_cost', 0.0):.4f}")
    
    if not runs:
        print("\n⚠️  No runs found in session memory")
        return
    
    print(f"\n📋 Most Recent Runs (showing last 5):")
    print(f"{'-'*70}")
    
    for i, run in enumerate(runs[:5], 1):
        print(f"\n{i}. Run ID: {run.get('id')}")
        print(f"   Trigger Type: {run.get('trigger_type', 'N/A')}")
        print(f"   Run Type: {run.get('run_type', 'N/A')}")
        print(f"   Status: {run.get('status', 'N/A')}")
        print(f"   Branch: {run.get('branch', 'N/A')}")
        print(f"   Commit: {run.get('commit_sha', 'N/A')[:7]}")
        
        if run.get('pr_number'):
            print(f"   PR: #{run.get('pr_number')} - {run.get('pr_title', 'N/A')}")
        
        if run.get('skip_reason'):
            print(f"   Skip Reason: {run.get('skip_reason')}")
        
        tasks = run.get('tasks', {})
        if tasks:
            print(f"   Tasks:")
            for task_name, task_result in tasks.items():
                status = task_result.get('status', 'unknown')
                print(f"     - {task_name}: {status}")

def check_api_endpoints(url="http://localhost:8080"):
    """Check various API endpoints."""
    print_section("API Endpoints Check")
    
    endpoints = [
        ("/api/metrics", "Dashboard Metrics"),
        ("/api/history", "Run History"),
        ("/api/trigger-config", "Trigger Configuration"),
    ]
    
    for endpoint, name in endpoints:
        try:
            response = requests.get(f"{url}{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"✅ {name} ({endpoint}): OK")
            else:
                print(f"⚠️  {name} ({endpoint}): Status {response.status_code}")
        except Exception as e:
            print(f"❌ {name} ({endpoint}): {e}")

def main():
    """Run comprehensive diagnostics."""
    print("\n" + "="*70)
    print("  PR-CENTRIC AUTOMATION FLOW DIAGNOSTICS")
    print("="*70)
    
    # Step 1: Check configuration
    if not check_configuration():
        print("\n❌ Configuration errors detected. Please fix .env file.")
        return 1
    
    # Step 2: Check server health
    if not check_server_health():
        print("\n❌ Server is not running. Start it with: python run_api.py")
        return 1
    
    # Step 3: Check API endpoints
    check_api_endpoints()
    
    # Step 4: Check existing session memory
    check_session_memory()
    
    # Step 5: Send test webhook
    print("\n" + "="*70)
    print("  SENDING TEST PR WEBHOOK")
    print("="*70)
    
    config = Config()
    webhook_url = "http://localhost:8080/webhook"
    
    # Test PR synchronize event
    payload = create_pr_payload(action="synchronize", pr_number=999)
    success = send_webhook(webhook_url, config.GITHUB_WEBHOOK_SECRET, payload)
    
    if success:
        print("\n✅ Webhook sent successfully!")
        print("\n⏳ Waiting 5 seconds for processing...")
        time.sleep(5)
        
        # Check session memory again
        check_session_memory()
        
        print("\n" + "="*70)
        print("  DIAGNOSTIC SUMMARY")
        print("="*70)
        print("✅ Configuration: Valid")
        print("✅ Server: Running")
        print("✅ Webhook: Accepted")
        print("\n📝 Check the server logs above for detailed execution flow")
        print("   Look for lines starting with [WEBHOOK], [HANDLER], [ORCHESTRATOR]")
        
    else:
        print("\n❌ Webhook failed!")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
