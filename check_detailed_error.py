#!/usr/bin/env python3
"""Check detailed error information from session memory."""
import json

with open('session_memory.json') as f:
    data = json.load(f)
    run = data['runs'][0]
    
print("="*80)
print(f"Run ID: {run['id']}")
print(f"Status: {run['status']}")
print("="*80)

print("\n📋 CODE REVIEW FULL DETAILS:")
print("-"*80)
cr = run['tasks']['code_review']
print(json.dumps(cr, indent=2))

print("\n📋 README UPDATE FULL DETAILS:")
print("-"*80)
readme = run['tasks']['readme_update']
print(json.dumps(readme, indent=2))

print("\n📋 SPEC UPDATE FULL DETAILS:")
print("-"*80)
spec = run['tasks']['spec_update']
print(json.dumps(spec, indent=2))

print("\n📊 AUTOMATION PR INFO:")
print("-"*80)
print(f"Automation PR Number: {run.get('automation_pr_number')}")
print(f"Automation PR Branch: {run.get('automation_pr_branch')}")

print("\n📊 DIFF ANALYSIS:")
print("-"*80)
diff = run.get('diff_analysis', {})
print(f"Total lines changed: {diff.get('total_lines_changed')}")
print(f"Code files changed: {len(diff.get('code_files_changed', []))}")
print(f"Has code changes: {diff.get('has_code_changes')}")
