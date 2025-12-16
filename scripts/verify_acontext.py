#!/usr/bin/env python3
"""
Verify Acontext API connectivity.

Run this script locally to confirm the agent can connect to your Acontext instance.

Usage:
    python scripts/verify_acontext.py [--url URL]

Default URL: http://localhost:8029/api/v1
"""

import asyncio
import argparse
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from automation_agent.memory import AcontextClient


async def verify_connection(api_url: str) -> bool:
    """Test Acontext connectivity with a simple session lifecycle."""
    print(f"\n🔍 Testing Acontext at: {api_url}\n")
    
    client = AcontextClient(
        api_url=api_url,
        storage_path="verify_test_memory.json",
        enabled=True,
        max_lessons=3,
    )
    
    # Test 1: Start session
    print("1️⃣  Starting test session...")
    success = await client.start_session(
        session_id="verify-test-001",
        pr_title="Test: Verify Acontext Connection",
        pr_files=["test.py"],
        branch="main",
    )
    
    if success:
        print("   ✅ Session started successfully")
    else:
        print("   ⚠️  Session started (using local fallback)")
    
    # Test 2: Log event
    print("2️⃣  Logging test event...")
    await client.log_event(
        session_id="verify-test-001",
        event_type="verification",
        data={"message": "Connection test"},
    )
    print("   ✅ Event logged")
    
    # Test 3: Finish session
    print("3️⃣  Finishing session...")
    await client.finish_session(
        session_id="verify-test-001",
        status="completed",
        summary="Verification test completed",
    )
    print("   ✅ Session finished")
    
    # Test 4: Query similar sessions
    print("4️⃣  Querying similar sessions...")
    results = await client.query_similar_sessions(
        pr_title="Test verification",
        pr_files=["test.py"],
    )
    print(f"   ✅ Found {len(results)} similar sessions")
    
    # Show stats
    stats = client.get_stats()
    print("\n📊 Stats:")
    print(f"   - Total sessions: {stats['total_sessions']}")
    print(f"   - API available: {stats['api_available']}")
    print(f"   - Enabled: {stats['enabled']}")
    
    # Final status
    if stats['api_available']:
        print("\n✅ SUCCESS - Agent connected to Acontext on port 8029")
        return True
    else:
        print("\n⚠️  WARNING - Using local fallback (Acontext API not reachable)")
        print("   Agent will still work, but won't share memory across instances.")
        return False


def main():
    parser = argparse.ArgumentParser(description="Verify Acontext API connectivity")
    parser.add_argument(
        "--url",
        default=os.getenv("ACONTEXT_API_URL", "http://localhost:8029/api/v1"),
        help="Acontext API URL (default: http://localhost:8029/api/v1)"
    )
    args = parser.parse_args()
    
    print("=" * 50)
    print("🧠 Acontext Connection Verification")
    print("=" * 50)
    
    success = asyncio.run(verify_connection(args.url))
    
    # Cleanup test file
    if os.path.exists("verify_test_memory.json"):
        os.remove("verify_test_memory.json")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
