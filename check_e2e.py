#!/usr/bin/env python3
"""Check E2E test results."""
import json

with open('session_memory.json', 'r') as f:
    data = json.load(f)

run = data['runs'][0]

print("="*80)
print("🧪 E2E Test Results")
print("="*80)
print(f"\n📋 Run Details:")
print(f"   Run ID: {run.get('id', 'N/A')}")
print(f"   Status: {run.get('status', 'unknown')}")
print(f"   Commit: {run.get('commit_sha', 'N/A')[:7]}")
print(f"   PR Number: {run.get('pr_number', 'N/A')}")

print(f"\n✅ Tasks:")
for task_name, task_data in run['tasks'].items():
    status = task_data.get('status', 'unknown')
    success = task_data.get('success', False)
    emoji = "✅" if success else "❌"
    print(f"   {emoji} {task_name}: {status}")
    
    if not success and 'error_type' in task_data:
        print(f"      Error: {task_data.get('error_type')} - {task_data.get('message', 'No message')}")

print(f"\n📊 Automation PR:")
automation_pr = run.get('automation_pr_number')
if automation_pr:
    print(f"   ✅ Created: PR #{automation_pr}")
    print(f"   Branch: {run.get('automation_pr_branch', 'N/A')}")
else:
    print(f"   ⚠️  Not created (check if content was generated)")

print(f"\n📈 Metrics:")
metrics = run.get('metrics', {})
if metrics:
    for key, value in metrics.items():
        print(f"   {key}: {value}")
else:
    print(f"   No metrics recorded")

print(f"\n" + "="*80)
if run['status'] == 'completed':
    print("🎉 E2E Test PASSED! All tasks completed successfully!")
elif run['status'] == 'completed_with_issues':
    print("⚠️  E2E Test completed with some issues. Check failed tasks above.")
else:
    print("❌ E2E Test FAILED. Check errors above.")
print("="*80)
