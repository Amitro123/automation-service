#!/usr/bin/env python3
"""
Debug Acontext Connection - Comprehensive diagnostics for port 8029.

This script performs:
1. Port scan to check if 8029 is listening
2. Raw TCP connection test
3. HTTP request inspection with detailed error reporting
4. Path discovery (common API endpoints)

Usage:
    python scripts/debug_acontext_connection.py [--host HOST] [--port PORT]
"""

import socket
import argparse
import sys
from urllib.parse import urljoin

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("⚠️  'requests' not installed, using basic socket tests only")


def check_port_open(host: str, port: int, timeout: float = 3.0) -> bool:
    """Check if a port is open using raw socket connection."""
    print(f"\n1️⃣  Port Scan: {host}:{port}")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"   ✅ Port {port} is OPEN")
            return True
        else:
            print(f"   ❌ Port {port} is CLOSED (error code: {result})")
            return False
    except socket.gaierror as e:
        print(f"   ❌ DNS resolution failed: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False


def test_tcp_connection(host: str, port: int) -> bool:
    """Test raw TCP connection and read response."""
    print(f"\n2️⃣  TCP Connection Test")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        sock.connect((host, port))
        
        # Send HTTP GET request
        request = f"GET /api/v1/health HTTP/1.1\r\nHost: {host}:{port}\r\n\r\n"
        sock.sendall(request.encode())
        
        # Read response
        response = sock.recv(4096).decode('utf-8', errors='ignore')
        sock.close()
        
        print(f"   ✅ TCP connection successful")
        print(f"   Response preview: {response[:200]}")
        return True
    except socket.timeout:
        print(f"   ❌ Connection timeout")
        return False
    except ConnectionRefusedError:
        print(f"   ❌ Connection refused (nothing listening on port)")
        return False
    except Exception as e:
        print(f"   ❌ TCP test failed: {e}")
        return False


def test_http_request(base_url: str) -> dict:
    """Test HTTP request with detailed error reporting."""
    print(f"\n3️⃣  HTTP Request Inspection")
    
    if not HAS_REQUESTS:
        print("   ⚠️  Skipping (requests library not available)")
        return {}
    
    endpoints = [
        "/api/v1/health",
        "/health",
        "/api/health",
        "/",
    ]
    
    results = {}
    
    for endpoint in endpoints:
        url = urljoin(base_url, endpoint)
        try:
            print(f"\n   Testing: {url}")
            response = requests.get(url, timeout=5)
            
            print(f"   ✅ Status: {response.status_code}")
            print(f"   Headers: {dict(response.headers)}")
            print(f"   Body preview: {response.text[:200]}")
            
            results[endpoint] = {
                "status": response.status_code,
                "success": True,
                "body": response.text[:500]
            }
            
        except requests.exceptions.ConnectionError as e:
            print(f"   ❌ Connection Error: {e}")
            results[endpoint] = {"success": False, "error": "connection_error"}
            
        except requests.exceptions.Timeout:
            print(f"   ❌ Timeout")
            results[endpoint] = {"success": False, "error": "timeout"}
            
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Request failed: {e}")
            results[endpoint] = {"success": False, "error": str(e)}
    
    return results


def discover_paths(base_url: str) -> None:
    """Try common API paths to discover what's available."""
    print(f"\n4️⃣  Path Discovery")
    
    if not HAS_REQUESTS:
        print("   ⚠️  Skipping (requests library not available)")
        return
    
    common_paths = [
        "/",
        "/api",
        "/api/v1",
        "/api/v1/health",
        "/api/v1/sessions",
        "/health",
        "/status",
        "/docs",
        "/openapi.json",
    ]
    
    print(f"\n   Scanning common paths...")
    found = []
    
    for path in common_paths:
        url = urljoin(base_url, path)
        try:
            response = requests.get(url, timeout=2)
            if response.status_code < 500:
                found.append((path, response.status_code))
                print(f"   ✅ {path} → {response.status_code}")
        except:
            pass
    
    if not found:
        print(f"   ❌ No paths responded")
    else:
        print(f"\n   Found {len(found)} accessible paths")


def check_firewall_and_services() -> None:
    """Check for common issues."""
    print(f"\n5️⃣  System Checks")
    
    # Check if running on Windows
    if sys.platform == "win32":
        print("   Platform: Windows")
        print("   💡 Tip: Check Windows Firewall if port is blocked")
        print("   💡 Run: netstat -ano | findstr :8029")
    else:
        print(f"   Platform: {sys.platform}")
        print("   💡 Run: lsof -i :8029")
    
    print("\n   Common issues:")
    print("   - Acontext not started (run: acontext docker up)")
    print("   - Wrong port (check Acontext config)")
    print("   - Firewall blocking localhost connections")
    print("   - Service crashed (check logs)")


def main():
    parser = argparse.ArgumentParser(description="Debug Acontext connection")
    parser.add_argument("--host", default="localhost", help="Host to test (default: localhost)")
    parser.add_argument("--port", type=int, default=8029, help="Port to test (default: 8029)")
    args = parser.parse_args()
    
    base_url = f"http://{args.host}:{args.port}"
    
    print("=" * 60)
    print("🔍 Acontext Connection Debugger")
    print("=" * 60)
    print(f"Target: {base_url}")
    
    # Run diagnostics
    port_open = check_port_open(args.host, args.port)
    
    if port_open:
        test_tcp_connection(args.host, args.port)
        test_http_request(base_url)
        discover_paths(base_url)
    else:
        print("\n⚠️  Port is not open, skipping HTTP tests")
    
    check_firewall_and_services()
    
    # Summary
    print("\n" + "=" * 60)
    if port_open:
        print("✅ Port is open - check HTTP response details above")
    else:
        print("❌ Port is closed - Acontext is likely not running")
    print("=" * 60)


if __name__ == "__main__":
    main()
