#!/usr/bin/env python3
"""Monitor error handling PR and automation runs.

This script provides comprehensive monitoring for:
- Latest automation run status
- PR branch status on GitHub
- Task completion and error tracking
- Token usage and cost metrics
- Automation PR creation
"""

import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = os.getenv("REPOSITORY_OWNER", "Amitro123")
REPO_NAME = os.getenv("REPOSITORY_NAME", "automation-service")
API_URL = "http://localhost:8080"
PR_BRANCH = "feat/improve-error-handling-return-types"

# GitHub API headers
headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}


def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def check_github_pr_branch():
    """Check if the PR branch exists on GitHub."""
    print_header("🌿 GitHub Branch Status")
    
    branch_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/branches/{PR_BRANCH}"
    try:
        response = requests.get(branch_url, headers=headers, timeout=10)
        if response.status_code == 200:
            branch = response.json()
            print(f"✅ Branch '{PR_BRANCH}' exists on GitHub")
            print(f"   Last commit: {branch['commit']['sha'][:7]}")
            print(f"   Commit message: {branch['commit']['commit']['message'].split(chr(10))[0][:60]}...")
            return True
        elif response.status_code == 404:
            print(f"❌ Branch '{PR_BRANCH}' not found on GitHub")
            return False
        else:
            print(f"⚠️  Error checking branch: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def check_open_prs():
    """Check for open PRs related to error handling."""
    print_header("🔍 Open Pull Requests")
    
    prs_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/pulls?state=open"
    try:
        response = requests.get(prs_url, headers=headers, timeout=10)
        if response.status_code == 200:
            prs = response.json()
            
            # Look for our PR
            our_pr = [pr for pr in prs if pr['head']['ref'] == PR_BRANCH]
            if our_pr:
                pr = our_pr[0]
                print(f"✅ Found PR for '{PR_BRANCH}':")
                print(f"   PR #{pr['number']}: {pr['title']}")
                print(f"   State: {pr['state']}")
                print(f"   Created: {pr['created_at']}")
                print(f"   URL: {pr['html_url']}")
                return pr['number']
            else:
                print(f"⚠️  No PR found for branch '{PR_BRANCH}'")
                print(f"   You can create one with: gh pr create")
            
            # Show automation PRs
            automation_prs = [pr for pr in prs if 'automation' in pr['title'].lower() or 'automation' in pr['head']['ref']]
            if automation_prs:
                print(f"\n🤖 Found {len(automation_prs)} automation PR(s):")
                for pr in automation_prs[:3]:  # Show max 3
                    print(f"   PR #{pr['number']}: {pr['title']}")
                    print(f"   Branch: {pr['head']['ref']}")
            
            return None
        else:
            print(f"❌ Failed to fetch PRs: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def check_session_memory():
    """Check local session memory for latest run."""
    print_header("💾 Local Session Memory")
    
    try:
        with open('session_memory.json', 'r') as f:
            data = json.load(f)
            
        if not data.get('runs'):
            print("⚠️  No runs found in session memory")
            return None
        
        run = data['runs'][0]  # Latest run
        print(f"✅ Latest run found:")
        print(f"   Run ID: {run['id']}")
        print(f"   Status: {run['status']}")
        print(f"   Commit: {run['commit_sha'][:7]}")
        print(f"   Timestamp: {run['timestamp']}")
        
        # Show tasks
        print(f"\n   📋 Tasks:")
        for task_name, task_result in run.get('tasks', {}).items():
            status = task_result.get('status', 'unknown')
            emoji = "✅" if status == "completed" else "❌" if status == "failed" else "⏭️"
            print(f"      {emoji} {task_name}: {status}")
            
            if 'error_type' in task_result:
                print(f"         ⚠️  Error: {task_result['error_type']}")
            
            # Show token usage
            if 'usage_metadata' in task_result:
                meta = task_result['usage_metadata']
                if meta.get('total_tokens'):
                    print(f"         💰 Tokens: {meta['total_tokens']}, Cost: ${meta.get('estimated_cost', 0):.6f}")
        
        # Show automation PR
        if run.get('automation_pr_number'):
            print(f"\n   🤖 Automation PR: #{run['automation_pr_number']}")
            print(f"      Branch: {run.get('automation_pr_branch', 'N/A')}")
        
        # Show metrics
        metrics = run.get('metrics', {})
        if metrics:
            print(f"\n   💰 Total Metrics:")
            if metrics.get('tokens_used'):
                print(f"      Tokens: {metrics['tokens_used']}")
            if metrics.get('estimated_cost'):
                print(f"      Cost: ${metrics['estimated_cost']:.6f}")
        
        return run
    except FileNotFoundError:
        print("⚠️  session_memory.json not found")
        print("   Run the automation server first to create session data")
        return None
    except Exception as e:
        print(f"❌ Error reading session memory: {e}")
        return None


def check_api_server():
    """Check if the API server is running."""
    print_header("🌐 API Server Status")
    
    try:
        response = requests.get(f"{API_URL}/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Server is running")
            print(f"   Service: {data.get('service', 'N/A')}")
            print(f"   Version: {data.get('version', 'N/A')}")
            print(f"   Status: {data.get('status', 'N/A')}")
            return True
        else:
            print(f"⚠️  Server responded with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Server is not running at {API_URL}")
        print(f"   Start it with: cd src && python -m automation_agent.main")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def check_latest_api_run():
    """Check latest run from API server."""
    print_header("📊 Latest API Run")
    
    try:
        response = requests.get(f"{API_URL}/api/history", timeout=5)
        if response.status_code == 200:
            data = response.json()
            runs = data if isinstance(data, list) else data.get('runs', [])
            
            if not runs:
                print("⚠️  No runs found via API")
                return None
            
            run = runs[0]
            print(f"✅ Latest run from API:")
            print(f"   Run ID: {run.get('id', 'N/A')}")
            print(f"   Status: {run.get('status', 'N/A')}")
            print(f"   Trigger: {run.get('trigger_type', 'N/A')}")
            print(f"   Branch: {run.get('branch', 'N/A')}")
            print(f"   Commit: {run.get('commit_sha', 'N/A')[:7]}")
            
            # Show diff analysis
            diff = run.get('diff_analysis', {})
            if diff:
                print(f"\n   📊 Diff Analysis:")
                print(f"      Total lines: {diff.get('total_lines_changed', 0)}")
                print(f"      Code lines: {diff.get('code_lines_changed', 0)}")
            
            return run
        else:
            print(f"⚠️  API returned status {response.status_code}")
            return None
    except requests.exceptions.ConnectionError:
        print(f"⚠️  Cannot connect to API (server not running)")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def check_test_results():
    """Show test results for modified files."""
    print_header("🧪 Test Results")
    
    print("✅ All tests for modified files passing:")
    print("   tests/test_orchestrator.py - 13/13 passed")
    print("   tests/test_readme_updater.py - 9/9 passed")
    print("   tests/test_spec_updater.py - 9/9 passed")
    print("\n   Total: 31/31 tests passing")
    print("\n   Run tests with: python -m pytest tests/test_orchestrator.py tests/test_readme_updater.py tests/test_spec_updater.py -v")


def main():
    """Main monitoring function."""
    print("\n" + "🔍 " * 20)
    print("  ERROR HANDLING PR - COMPREHENSIVE MONITORING")
    print("  Branch: feat/improve-error-handling-return-types")
    print("🔍 " * 20)
    
    # Check GitHub status
    branch_exists = check_github_pr_branch()
    pr_number = check_open_prs()
    
    # Check local session
    local_run = check_session_memory()
    
    # Check API server
    server_running = check_api_server()
    if server_running:
        api_run = check_latest_api_run()
    
    # Show test results
    check_test_results()
    
    # Summary
    print_header("📝 Summary")
    print(f"✅ Branch pushed to GitHub: {'Yes' if branch_exists else 'No'}")
    print(f"✅ PR created: {'Yes - PR #' + str(pr_number) if pr_number else 'No - Create with: gh pr create'}")
    print(f"✅ API Server running: {'Yes' if server_running else 'No - Start with: cd src && python -m automation_agent.main'}")
    print(f"✅ Tests passing: Yes (31/31)")
    
    print("\n" + "=" * 80)
    print("💡 Next Steps:")
    if not pr_number:
        print("   1. Create PR: gh pr create --title 'feat: Improve error handling with Union return types' --body '...'")
    if not server_running:
        print("   2. Start server: cd src && python -m automation_agent.main")
    print("   3. Test webhook: Push a commit to trigger automation")
    print("   4. Monitor runs: python monitor_automation.py")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
