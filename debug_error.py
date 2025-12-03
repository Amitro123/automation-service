#!/usr/bin/env python3
"""Debug script to find the code review error."""
import json

with open('session_memory.json') as f:
    data = json.load(f)
    run = data['runs'][0]
    
print("="*80)
print(f"Run ID: {run['id']}")
print(f"Status: {run['status']}")
print("="*80)

print("\n📋 CODE REVIEW TASK DETAILS:")
print("-"*80)
cr = run['tasks']['code_review']
for key, value in cr.items():
    print(f"{key}: {value}")

print("\n📋 ALL TASKS:")
print("-"*80)
for task_name, task_data in run['tasks'].items():
    print(f"\n{task_name}:")
    print(f"  Status: {task_data.get('status')}")
    print(f"  Success: {task_data.get('success')}")
    if 'error' in task_data:
        print(f"  Error: {task_data['error']}")
    if 'error_type' in task_data:
        print(f"  Error Type: {task_data['error_type']}")
    if 'message' in task_data:
        print(f"  Message: {task_data['message'][:200]}...")

print("\n📊 RUN SUMMARY:")
print("-"*80)
print(f"Failed Tasks: {run.get('failed_tasks', [])}")
print(f"Failure Reasons: {run.get('failure_reasons', {})}")
print(f"Automation PR: {run.get('automation_pr_number')}")
