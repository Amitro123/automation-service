#!/usr/bin/env python3
"""Test PR diff fetching."""
import asyncio
from dotenv import load_dotenv
from src.automation_agent.config import Config
from src.automation_agent.github_client import GitHubClient

load_dotenv()

async def test_diff_fetch():
    """Test fetching PR #92 diff."""
    config = Config()
    github = GitHubClient(config, config.REPOSITORY_OWNER, config.REPOSITORY_NAME)
    
    pr_number = 92
    
    print("="*80)
    print(f"🧪 Testing PR #{pr_number} Diff Fetch")
    print("="*80)
    
    print(f"\n📄 Fetching diff...")
    diff = await github.get_pull_request_diff(pr_number)
    
    if diff:
        print(f"✅ Diff fetched successfully!")
        print(f"   Length: {len(diff)} chars")
        print(f"   Lines: {len(diff.split(chr(10)))}")
        
        # Count actual changes
        additions = sum(1 for line in diff.split('\n') if line.startswith('+') and not line.startswith('+++'))
        deletions = sum(1 for line in diff.split('\n') if line.startswith('-') and not line.startswith('---'))
        
        print(f"   Additions: +{additions}")
        print(f"   Deletions: -{deletions}")
        print(f"   Total changes: {additions + deletions}")
        
        print(f"\n📝 First 20 lines:")
        for i, line in enumerate(diff.split('\n')[:20], 1):
            print(f"   {i:2d}: {line}")
        
        print(f"\n✅ Diff is valid and should NOT be skipped!")
    else:
        print(f"❌ Failed to fetch diff!")
        print(f"   This would cause the run to be skipped.")
    
    print("="*80)

if __name__ == "__main__":
    asyncio.run(test_diff_fetch())
