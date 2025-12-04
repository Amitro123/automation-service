#!/usr/bin/env python3
"""Debug empty diff issue for PR #92."""
import os
import asyncio
from dotenv import load_dotenv
from src.automation_agent.github_client import GitHubClient
from src.automation_agent.config import Config

load_dotenv()

async def debug_pr_diff():
    """Check PR #92 diff."""
    config = Config()
    github = GitHubClient(config, config.REPOSITORY_OWNER, config.REPOSITORY_NAME)
    
    pr_number = 92
    commit_sha = "b6965e4"
    
    print("="*80)
    print(f"🔍 Debugging PR #{pr_number} - Commit {commit_sha}")
    print("="*80)
    
    # Get PR details
    print(f"\n📋 Fetching PR details...")
    pr_url = f"https://api.github.com/repos/{config.REPOSITORY_OWNER}/{config.REPOSITORY_NAME}/pulls/{pr_number}"
    pr_data = await github._make_request("GET", pr_url)
    
    if pr_data:
        print(f"   Title: {pr_data.get('title')}")
        print(f"   State: {pr_data.get('state')}")
        print(f"   Head SHA: {pr_data.get('head', {}).get('sha', 'N/A')[:7]}")
        print(f"   Base SHA: {pr_data.get('base', {}).get('sha', 'N/A')[:7]}")
        print(f"   Commits: {pr_data.get('commits', 0)}")
        print(f"   Changed Files: {pr_data.get('changed_files', 0)}")
        print(f"   Additions: {pr_data.get('additions', 0)}")
        print(f"   Deletions: {pr_data.get('deletions', 0)}")
    
    # Get commit details
    print(f"\n📝 Fetching commit details...")
    commit_url = f"https://api.github.com/repos/{config.REPOSITORY_OWNER}/{config.REPOSITORY_NAME}/commits/{commit_sha}"
    commit_data = await github._make_request("GET", commit_url)
    
    if commit_data:
        print(f"   Message: {commit_data.get('commit', {}).get('message', 'N/A').split(chr(10))[0]}")
        print(f"   Author: {commit_data.get('commit', {}).get('author', {}).get('name', 'N/A')}")
        stats = commit_data.get('stats', {})
        print(f"   Stats: +{stats.get('additions', 0)} -{stats.get('deletions', 0)} total={stats.get('total', 0)}")
        files = commit_data.get('files', [])
        print(f"   Files changed: {len(files)}")
        if files:
            for f in files[:5]:
                print(f"      - {f.get('filename')} (+{f.get('additions', 0)} -{f.get('deletions', 0)})")
    
    # Get diff
    print(f"\n📄 Fetching diff...")
    try:
        diff = await github.get_commit_diff(commit_sha)
        print(f"   Diff length: {len(diff)} chars")
        if diff:
            lines = diff.split('\n')
            print(f"   Diff lines: {len(lines)}")
            print(f"\n   First 10 lines:")
            for line in lines[:10]:
                print(f"      {line}")
        else:
            print(f"   ❌ Diff is empty!")
    except Exception as e:
        print(f"   ❌ Error fetching diff: {e}")
    
    # Check if this is a merge commit
    if commit_data:
        parents = commit_data.get('parents', [])
        print(f"\n🔀 Commit type:")
        if len(parents) > 1:
            print(f"   ⚠️  MERGE COMMIT (has {len(parents)} parents)")
            print(f"   This might explain the empty diff!")
        else:
            print(f"   ✅ Regular commit (1 parent)")
    
    print("\n" + "="*80)
    print("💡 Diagnosis:")
    print("="*80)
    
    if pr_data:
        if pr_data.get('additions', 0) == 0 and pr_data.get('deletions', 0) == 0:
            print("❌ PR has no changes (additions=0, deletions=0)")
            print("   Possible reasons:")
            print("   1. Empty commit (git commit --allow-empty)")
            print("   2. Merge commit with no conflicts")
            print("   3. Force push that replaced commit with identical content")
        elif not diff:
            print("❌ Diff fetch failed but PR has changes")
            print("   Possible reasons:")
            print("   1. GitHub API rate limit")
            print("   2. Commit not yet available")
            print("   3. Network error")
        else:
            print("✅ PR has changes, diff should be available")
    
    print("="*80)

if __name__ == "__main__":
    asyncio.run(debug_pr_diff())
