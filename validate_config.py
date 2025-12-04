#!/usr/bin/env python3
"""Quick script to validate .env configuration before starting server."""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

def validate_configuration():
    """Validate all required environment variables.
    
    Returns:
        bool: True if all required variables are set, False otherwise
    """
    print("=" * 80)
    print("🔍 CONFIGURATION VALIDATION")
    print("=" * 80)

    required_configs = {
        "GITHUB_TOKEN": os.getenv("GITHUB_TOKEN"),
        "GITHUB_WEBHOOK_SECRET": os.getenv("GITHUB_WEBHOOK_SECRET"),
        "REPOSITORY_OWNER": os.getenv("REPOSITORY_OWNER"),
        "REPOSITORY_NAME": os.getenv("REPOSITORY_NAME"),
    }

    llm_configs = {
        "LLM_PROVIDER": os.getenv("LLM_PROVIDER", "gemini"),
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
    }

    print("\n📋 Required GitHub Configuration:")
    all_valid = True
    for key, value in required_configs.items():
        if value:
            masked = value[:4] + "..." + value[-4:] if len(value) > 8 else "***"
            print(f"   ✅ {key}: {masked}")
        else:
            print(f"   ❌ {key}: NOT SET")
            all_valid = False

    print("\n🤖 LLM Configuration:")
    provider = llm_configs["LLM_PROVIDER"]
    print(f"   Provider: {provider}")

if provider == "gemini":
    if llm_configs["GEMINI_API_KEY"]:
        print(f"   ✅ GEMINI_API_KEY: Set")
    else:
        print(f"   ❌ GEMINI_API_KEY: NOT SET")
        all_valid = False
elif provider == "openai":
    if llm_configs["OPENAI_API_KEY"]:
        print(f"   ✅ OPENAI_API_KEY: Set")
    else:
        print(f"   ❌ OPENAI_API_KEY: NOT SET")
        all_valid = False
elif provider == "anthropic":
    if llm_configs["ANTHROPIC_API_KEY"]:
        print(f"   ✅ ANTHROPIC_API_KEY: Set")
    else:
        print(f"   ❌ ANTHROPIC_API_KEY: NOT SET")
        all_valid = False

print("\n" + "=" * 80)
if all_valid:
    print("✅ Configuration is valid! You can start the server.")
    print("\nRun: cd src && python -m automation_agent.main")
else:
    print("❌ Configuration is incomplete. Please update your .env file.")
    print("\nMissing values should be set to:")
    if not required_configs["REPOSITORY_OWNER"]:
        print("   REPOSITORY_OWNER=Amitro123")
    if not required_configs["REPOSITORY_NAME"]:
        print("   REPOSITORY_NAME=automation-service")
    if not required_configs["GITHUB_TOKEN"]:
        print("   GITHUB_TOKEN=<your_github_token>")
    if not required_configs["GITHUB_WEBHOOK_SECRET"]:
        print("   GITHUB_WEBHOOK_SECRET=<your_webhook_secret>")
    
    if provider == "gemini" and not llm_configs["GEMINI_API_KEY"]:
        print("   GEMINI_API_KEY=<your_gemini_key>")

print("=" * 80)
