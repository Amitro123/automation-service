#!/usr/bin/env python3
"""Simple check for PR #92 diff."""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("GITHUB_TOKEN")
owner = os.getenv("REPOSITORY_OWNER")
repo = os.getenv("REPOSITORY_NAME")

pr_number = 92
commit_sha = "b6965e4"

headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github.v3+json"
}

print("="*80)
print(f"🔍 Checking PR #{pr_number} - Commit {commit_sha}")
print("="*80)

# Get PR details
print(f"\n📋 PR Details:")
pr_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
response = requests.get(pr_url, headers=headers)
if response.status_code == 200:
    pr_data = response.json()
    print(f"   Title: {pr_data.get('title')}")
    print(f"   State: {pr_data.get('state')}")
    print(f"   Head SHA: {pr_data.get('head', {}).get('sha', 'N/A')[:7]}")
    print(f"   Commits: {pr_data.get('commits', 0)}")
    print(f"   Files Changed: {pr_data.get('changed_files', 0)}")
    print(f"   Additions: +{pr_data.get('additions', 0)}")
    print(f"   Deletions: -{pr_data.get('deletions', 0)}")
else:
    print(f"   ❌ Error: {response.status_code}")

# Get commit details
print(f"\n📝 Commit Details:")
commit_url = f"https://api.github.com/repos/{owner}/{repo}/commits/{commit_sha}"
response = requests.get(commit_url, headers=headers)
if response.status_code == 200:
    commit_data = response.json()
    print(f"   Message: {commit_data.get('commit', {}).get('message', 'N/A').split(chr(10))[0]}")
    stats = commit_data.get('stats', {})
    print(f"   Stats: +{stats.get('additions', 0)} -{stats.get('deletions', 0)} (total: {stats.get('total', 0)})")
    files = commit_data.get('files', [])
    print(f"   Files: {len(files)}")
    if files:
        for f in files[:10]:
            print(f"      - {f.get('filename')} (+{f.get('additions', 0)} -{f.get('deletions', 0)})")
    
    # Check if merge commit
    parents = commit_data.get('parents', [])
    if len(parents) > 1:
        print(f"\n   ⚠️  MERGE COMMIT ({len(parents)} parents)")
else:
    print(f"   ❌ Error: {response.status_code}")

# Get diff
print(f"\n📄 Diff:")
diff_url = f"https://api.github.com/repos/{owner}/{repo}/commits/{commit_sha}"
response = requests.get(diff_url, headers={**headers, "Accept": "application/vnd.github.v3.diff"})
if response.status_code == 200:
    diff = response.text
    print(f"   Length: {len(diff)} chars")
    print(f"   Lines: {len(diff.split(chr(10)))}")
    if diff:
        lines = diff.split('\n')[:15]
        print(f"\n   First 15 lines:")
        for line in lines:
            print(f"      {line}")
    else:
        print(f"   ❌ Empty diff!")
else:
    print(f"   ❌ Error: {response.status_code}")

print("\n" + "="*80)
print("💡 Summary:")
print("="*80)

if response.status_code == 200 and not diff:
    print("❌ Diff is empty - this is why automation was skipped!")
    print("\nPossible reasons:")
    print("1. Empty commit (git commit --allow-empty)")
    print("2. Merge commit with no actual changes")
    print("3. Commit was amended/force-pushed with identical content")
    print("4. GitHub hasn't generated the diff yet (rare)")
elif response.status_code == 200 and diff:
    print("✅ Diff exists - automation should have run!")
    print("\nCheck orchestrator logs for why it was marked as empty.")
else:
    print(f"❌ Could not fetch diff (status: {response.status_code})")

print("="*80)
