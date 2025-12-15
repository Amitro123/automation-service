#!/usr/bin/env python3
"""
Seed script for importing historical automation logs into Acontext.

This script reads existing session_memory.json and imports the data
into the real Acontext API for long-term storage and similarity search.

Requirements:
- Acontext running on port 8029 (acontext docker up)
- Existing session_memory.json with historical runs

Usage:
    python scripts/seed_acontext.py [--api-url URL] [--source-file FILE]
"""

import asyncio
import aiohttp
import json
import argparse
import os
import sys
from datetime import datetime
from typing import Dict, List, Any

# Default configuration
DEFAULT_API_URL = "http://localhost:8029/api/v1"
DEFAULT_SOURCE_FILE = "session_memory.json"


async def import_session(
    session: aiohttp.ClientSession,
    api_url: str,
    run_data: Dict[str, Any]
) -> bool:
    """Import a single session into Acontext."""
    session_id = run_data.get("id", run_data.get("run_id", ""))
    
    if not session_id:
        print(f"  ⚠ Skipping run without ID")
        return False
    
    # Build session data
    session_data = {
        "session_id": session_id,
        "pr_title": run_data.get("pr_title", run_data.get("commit_message", "Unknown")),
        "pr_files": run_data.get("files", []),
        "branch": run_data.get("branch", "main"),
        "pr_number": run_data.get("pr_number"),
        "started_at": run_data.get("started_at", run_data.get("timestamp", datetime.now().isoformat())),
        "status": run_data.get("status", "completed"),
        "events": [],
        "key_lessons": [],
        "error_types": [],
    }
    
    # Extract lessons from task results
    tasks = run_data.get("tasks", {})
    for task_name, task_result in tasks.items():
        if isinstance(task_result, dict):
            if task_result.get("status") == "success":
                session_data["key_lessons"].append(f"{task_name}: completed successfully")
            elif task_result.get("status") == "failed":
                error_msg = task_result.get("error", task_result.get("message", "unknown"))
                session_data["error_types"].append(task_result.get("error_type", "unknown"))
                session_data["key_lessons"].append(f"{task_name} failed: {error_msg[:100]}")
    
    # Post to API
    try:
        async with session.post(
            f"{api_url}/sessions",
            json=session_data,
            timeout=aiohttp.ClientTimeout(total=10)
        ) as resp:
            if resp.status in (200, 201):
                print(f"  ✓ Imported session: {session_id}")
                return True
            elif resp.status == 409:
                print(f"  ⏭ Session already exists: {session_id}")
                return True
            else:
                error = await resp.text()
                print(f"  ✗ Failed to import {session_id}: {resp.status} - {error[:100]}")
                return False
    except Exception as e:
        print(f"  ✗ Error importing {session_id}: {e}")
        return False


async def seed_acontext(api_url: str, source_file: str) -> None:
    """Import all sessions from source file into Acontext."""
    
    # Check API availability
    print(f"🔍 Checking Acontext API at {api_url}...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{api_url}/health", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status != 200:
                    print(f"❌ Acontext API returned {resp.status}")
                    print("   Make sure to run: acontext docker up")
                    return
                print("✓ Acontext API is available")
    except aiohttp.ClientError as e:
        print(f"❌ Cannot connect to Acontext API: {e}")
        print("   Make sure to run: acontext docker up")
        return
    
    # Load source data
    if not os.path.exists(source_file):
        print(f"❌ Source file not found: {source_file}")
        return
    
    print(f"📂 Loading data from {source_file}...")
    with open(source_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Handle both formats: list of runs or dict with "runs" key
    runs: List[Dict[str, Any]] = []
    if isinstance(data, list):
        runs = data
    elif isinstance(data, dict):
        runs = data.get("runs", data.get("history", []))
    
    if not runs:
        print("⚠ No runs found in source file")
        return
    
    print(f"📤 Importing {len(runs)} sessions...")
    
    # Import sessions
    success_count = 0
    async with aiohttp.ClientSession() as session:
        for i, run in enumerate(runs, 1):
            print(f"\n[{i}/{len(runs)}]")
            if await import_session(session, api_url, run):
                success_count += 1
    
    # Summary
    print(f"\n{'='*50}")
    print(f"✅ Import complete: {success_count}/{len(runs)} sessions imported")
    
    if success_count > 0:
        print("\n🎉 Acontext is now seeded with historical data!")
        print("   The agent will use these lessons for future reviews.")


def main():
    parser = argparse.ArgumentParser(
        description="Seed Acontext with historical automation logs"
    )
    parser.add_argument(
        "--api-url",
        default=os.getenv("ACONTEXT_API_URL", DEFAULT_API_URL),
        help=f"Acontext API URL (default: {DEFAULT_API_URL})"
    )
    parser.add_argument(
        "--source-file",
        default=DEFAULT_SOURCE_FILE,
        help=f"Source JSON file with session history (default: {DEFAULT_SOURCE_FILE})"
    )
    
    args = parser.parse_args()
    
    print("="*50)
    print("🌱 Acontext Seed Script")
    print("="*50)
    
    asyncio.run(seed_acontext(args.api_url, args.source_file))


if __name__ == "__main__":
    main()
