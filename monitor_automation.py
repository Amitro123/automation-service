#!/usr/bin/env python3
"""Monitor automation runs in real-time."""

import requests
import json
import time
from datetime import datetime

API_URL = "http://localhost:8080"

def get_latest_run():
    """Fetch the latest automation run."""
    try:
        response = requests.get(f"{API_URL}/api/history", timeout=5)
        if response.status_code == 200:
            data = response.json()
            # API returns list directly or dict with "runs" key
            if isinstance(data, list) and len(data) > 0:
                return data[0]
            elif isinstance(data, dict) and data.get("runs"):
                return data["runs"][0]
        return None
    except Exception as e:
        print(f"❌ Error fetching runs: {e}")
        return None

def format_run(run):
    """Format run data for display."""
    print("\n" + "="*80)
    print(f"🆔 Run ID: {run.get('id', 'N/A')}")
    print(f"📅 Timestamp: {run.get('timestamp', 'N/A')}")
    print(f"🔀 Trigger: {run.get('trigger_type', 'N/A')}")
    print(f"📊 Status: {run.get('status', 'N/A')}")
    print(f"🌿 Branch: {run.get('branch', 'N/A')}")
    print(f"📝 Commit: {run.get('commit_sha', 'N/A')[:7]}")
    
    if run.get('pr_number'):
        print(f"🔗 PR: #{run['pr_number']} - {run.get('pr_title', 'N/A')}")
    
    # Diff analysis
    diff = run.get('diff_analysis', {})
    if diff:
        print(f"\n📊 Diff Analysis:")
        print(f"   Total lines: {diff.get('total_lines_changed', 0)}")
        print(f"   Code lines: {diff.get('code_lines_changed', 0)}")
        print(f"   Doc lines: {diff.get('doc_lines_changed', 0)}")
    
    # Tasks
    tasks = run.get('tasks', {})
    if tasks:
        print(f"\n✅ Tasks:")
        for task_name, task_result in tasks.items():
            status = task_result.get('status', 'unknown')
            emoji = "✅" if status == "completed" else "❌" if status == "failed" else "⏭️"
            print(f"   {emoji} {task_name}: {status}")
            
            # Show usage metadata if available
            if 'usage_metadata' in task_result:
                meta = task_result['usage_metadata']
                if meta.get('total_tokens'):
                    print(f"      💰 Tokens: {meta['total_tokens']}, Cost: ${meta.get('estimated_cost', 0):.6f}")
    
    # Metrics
    metrics = run.get('metrics', {})
    if metrics:
        print(f"\n💰 Metrics:")
        if metrics.get('tokens_used'):
            print(f"   Tokens: {metrics['tokens_used']}")
        if metrics.get('estimated_cost'):
            print(f"   Cost: ${metrics['estimated_cost']:.6f}")
    
    # Automation PR
    if run.get('automation_pr_number'):
        print(f"\n🤖 Automation PR: #{run['automation_pr_number']}")
        print(f"   Branch: {run.get('automation_pr_branch', 'N/A')}")
    
    print("="*80)

def monitor():
    """Monitor for new automation runs."""
    print("🔍 Monitoring automation runs...")
    print(f"📡 API: {API_URL}")
    print("Press Ctrl+C to stop\n")
    
    last_run_id = None
    
    while True:
        try:
            run = get_latest_run()
            if run and run.get('id') != last_run_id:
                print(f"\n🆕 NEW RUN DETECTED at {datetime.now().strftime('%H:%M:%S')}")
                format_run(run)
                last_run_id = run.get('id')
            
            time.sleep(2)  # Check every 2 seconds
            
        except KeyboardInterrupt:
            print("\n\n👋 Monitoring stopped.")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    # Show current latest run first
    print("📊 Current Latest Run:")
    run = get_latest_run()
    if run:
        format_run(run)
    else:
        print("No runs found yet.")
    
    print("\n" + "="*80)
    input("Press Enter to start monitoring for new runs...")
    monitor()
