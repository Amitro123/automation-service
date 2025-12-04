#!/usr/bin/env python3
"""Test GitHub token validity."""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("GITHUB_TOKEN")
owner = os.getenv("REPOSITORY_OWNER")
repo = os.getenv("REPOSITORY_NAME")

print("="*80)
print("🔑 Testing GitHub Token")
print("="*80)

print(f"\n📋 Configuration:")
print(f"   Token: {'*' * 30}{token[-10:] if token else 'NOT SET'}")
print(f"   Owner: {owner}")
print(f"   Repo: {repo}")

# Test 1: User info
print(f"\n🧪 Test 1: Get user info...")
headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github.v3+json"
}
response = requests.get("https://api.github.com/user", headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    user = response.json()
    print(f"   ✅ User: {user.get('login')}")
else:
    print(f"   ❌ Error: {response.text[:200]}")

# Test 2: Repo access
print(f"\n🧪 Test 2: Get repo info...")
response = requests.get(f"https://api.github.com/repos/{owner}/{repo}", headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    repo_data = response.json()
    print(f"   ✅ Repo: {repo_data.get('full_name')}")
    print(f"   Private: {repo_data.get('private')}")
else:
    print(f"   ❌ Error: {response.text[:200]}")

# Test 3: PR access
print(f"\n🧪 Test 3: Get PR #92...")
response = requests.get(f"https://api.github.com/repos/{owner}/{repo}/pulls/92", headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    pr = response.json()
    print(f"   ✅ PR: {pr.get('title')}")
    print(f"   State: {pr.get('state')}")
else:
    print(f"   ❌ Error: {response.text[:200]}")

# Test 4: PR diff
print(f"\n🧪 Test 4: Get PR #92 diff...")
diff_headers = {**headers, "Accept": "application/vnd.github.v3.diff"}
response = requests.get(f"https://api.github.com/repos/{owner}/{repo}/pulls/92", headers=diff_headers)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    diff = response.text
    print(f"   ✅ Diff length: {len(diff)} chars")
    print(f"   Lines: {len(diff.split(chr(10)))}")
else:
    print(f"   ❌ Error: {response.text[:200]}")

print("\n" + "="*80)
print("💡 Summary:")
print("="*80)

if response.status_code == 200:
    print("✅ GitHub token is valid and has correct permissions!")
    print("   The 401 error must be coming from something else.")
else:
    print("❌ GitHub token has issues!")
    print("\n🔧 Solutions:")
    print("1. Generate a new token at: https://github.com/settings/tokens")
    print("2. Required scopes: repo, pull_requests")
    print("3. Update GITHUB_TOKEN in .env")

print("="*80)
