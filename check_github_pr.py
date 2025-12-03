#!/usr/bin/env python3
"""Check GitHub PR #67 and look for automation PRs."""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = os.getenv("REPOSITORY_OWNER")
REPO_NAME = os.getenv("REPOSITORY_NAME")

headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

print("="*80)
print("🔍 Checking GitHub PR #67")
print("="*80)

# Check PR #67
pr_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/pulls/67"
response = requests.get(pr_url, headers=headers, timeout=10)
if response.status_code == 200:
    pr = response.json()
    print(f"\n✅ PR #67 Found:")
    print(f"   Title: {pr['title']}")
    print(f"   State: {pr['state']}")
    print(f"   Branch: {pr['head']['ref']}")
    print(f"   Base: {pr['base']['ref']}")
else:
    print(f"\n❌ Failed to fetch PR #67: {response.status_code}")

# Check for review comments on PR #67
print("\n" + "="*80)
print("💬 Checking for Review Comments on PR #67")
print("="*80)

reviews_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/pulls/67/reviews"
response = requests.get(reviews_url, headers=headers)

if response.status_code == 200:
    reviews = response.json()
    print(f"\n✅ Found {len(reviews)} reviews")
    for i, review in enumerate(reviews[-3:], 1):  # Show last 3
        print(f"\n   Review {i}:")
        print(f"   User: {review['user']['login']}")
        print(f"   State: {review['state']}")
        print(f"   Submitted: {review['submitted_at']}")
        if review['body']:
            print(f"   Body: {review['body'][:100]}...")
else:
    print(f"\n❌ Failed to fetch reviews: {response.status_code}")

# Check for all open PRs (look for automation PR)
print("\n" + "="*80)
print("🤖 Checking for Automation PRs")
print("="*80)

prs_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/pulls?state=open"
response = requests.get(prs_url, headers=headers)

if response.status_code == 200:
    prs = response.json()
    automation_prs = [pr for pr in prs if 'automation' in pr['title'].lower() or 'automation' in pr['head']['ref']]
    
    if automation_prs:
        print(f"\n✅ Found {len(automation_prs)} automation PR(s):")
        for pr in automation_prs:
            print(f"\n   PR #{pr['number']}: {pr['title']}")
            print(f"   Branch: {pr['head']['ref']}")
            print(f"   Created: {pr['created_at']}")
    else:
        print("\n❌ No automation PRs found")
else:
    print(f"\n❌ Failed to fetch PRs: {response.status_code}")

# Check for branches with 'automation' in name
print("\n" + "="*80)
print("🌿 Checking for Automation Branches")
print("="*80)

branches_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/branches"
response = requests.get(branches_url, headers=headers)

if response.status_code == 200:
    branches = response.json()
    automation_branches = [b for b in branches if 'automation' in b['name']]
    
    if automation_branches:
        print(f"\n✅ Found {len(automation_branches)} automation branch(es):")
        for branch in automation_branches:
            print(f"   - {branch['name']}")
    else:
        print("\n❌ No automation branches found")
else:
    print(f"\n❌ Failed to fetch branches: {response.status_code}")

print("\n" + "="*80)
