#!/usr/bin/env python
"""Quick script to check if the server is running."""

import requests
import sys

def check_server(url="http://localhost:8080"):
    """Check if server is responding."""
    try:
        response = requests.get(f"{url}/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Server is running!")
            print(f"   Status: {data.get('status')}")
            print(f"   Service: {data.get('service')}")
            print(f"   Version: {data.get('version')}")
            print(f"   Uptime: {data.get('uptime')}")
            return True
        else:
            print(f"❌ Server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to server at {url}")
        print(f"   Make sure the server is running: python run_api.py")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"
    success = check_server(url)
    sys.exit(0 if success else 1)
