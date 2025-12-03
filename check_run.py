#!/usr/bin/env python3
"""Quick script to check latest run status."""
import json

with open('session_memory.json') as f:
    data = json.load(f)
    run = data['runs'][0]
    
print(f"Run: {run['id']}")
print(f"Status: {run['status']}")
print(f"Commit: {run['commit_sha'][:7]}")
print(f"\nTasks:")
for task_name, task_result in run['tasks'].items():
    status = task_result.get('status', 'unknown')
    emoji = "✅" if status == "completed" else "❌" if status == "failed" else "⏭️"
    print(f"  {emoji} {task_name}: {status}")
    if 'error_type' in task_result:
        print(f"     Error: {task_result.get('error_type')}")

print(f"\nAutomation PR: {run.get('automation_pr_number', 'None')}")
print(f"Metrics: {run.get('metrics', {})}")
