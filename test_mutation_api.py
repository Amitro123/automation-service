"""Test script for mutation testing API endpoints."""

import requests
import time

BASE_URL = "http://localhost:8080"

print("Testing Mutation Testing API Endpoints")
print("=" * 50)

# Test 1: Check if mutation testing is enabled
print("\n1. Checking if mutation testing is enabled...")
print("   (Make sure ENABLE_MUTATION_TESTS=True in .env)")

# Test 2: Trigger mutation tests
print("\n2. Triggering mutation tests...")
try:
    response = requests.post(f"{BASE_URL}/api/mutation/run")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    if response.status_code == 200:
        print("   ✅ Mutation tests started successfully!")
        print("   ⏳ Tests are running in background (this may take several minutes)...")
    elif response.status_code == 400:
        print("   ⚠️  Mutation testing is disabled.")
        print("   💡 Enable it by setting ENABLE_MUTATION_TESTS=True in .env")
        print("   💡 Then restart the API server")
        exit(1)
except Exception as e:
    print(f"   ❌ Error: {e}")
    print("   💡 Make sure the API server is running (python run_api.py)")
    exit(1)

# Test 3: Wait a bit and check results
print("\n3. Waiting 5 seconds before checking results...")
time.sleep(5)

print("\n4. Fetching mutation test results...")
try:
    response = requests.get(f"{BASE_URL}/api/mutation/results")
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        results = response.json()
        print(f"   ✅ Results retrieved!")
        print(f"\n   Mutation Score: {results.get('mutation_score', 0)}%")
        print(f"   Total Mutants: {results.get('mutants_total', 0)}")
        print(f"   Killed: {results.get('mutants_killed', 0)}")
        print(f"   Survived: {results.get('mutants_survived', 0)}")
        print(f"   Last Run: {results.get('last_run_time', 'N/A')}")
    elif response.status_code == 404:
        print("   ⏳ Results not available yet (tests still running or not started)")
        print("   💡 Wait a few more minutes and try again")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 5: Check /api/metrics
print("\n5. Checking if /api/metrics shows mutation score...")
try:
    response = requests.get(f"{BASE_URL}/api/metrics")
    if response.status_code == 200:
        data = response.json()
        mutation_score = data.get('coverage', {}).get('mutationScore', 0)
        print(f"   ✅ Mutation Score in /api/metrics: {mutation_score}%")
        if mutation_score > 0:
            print("   ✅ Real mutation score is being displayed!")
        else:
            print("   ⚠️  Mutation score is 0 (no results yet or tests not run)")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 50)
print("Testing complete!")
print("\nNote: Mutation tests can take 5-10 minutes to complete.")
print("Check the API server logs for progress.")
