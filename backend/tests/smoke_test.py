#!/usr/bin/env python3
"""
Quick API Test Runner
Runs essential smoke tests to verify API is working
"""

import requests
import sys

BASE_URL = "http://localhost:3000/api/v1"

def check(endpoint, method="GET", **kwargs):
    """Quick check helper"""
    url = f"{BASE_URL}{endpoint}"
    r = None
    try:
        if method == "GET":
            r = requests.get(url, **kwargs)
        elif method == "POST":
            r = requests.post(url, **kwargs)
        
        if r:
            status = "✓" if r.status_code < 400 else "✗"
            print(f"{status} [{r.status_code}] {method} {endpoint}")
            return r.status_code < 400
        return False
    except Exception as e:
        print(f"✗ [ERR] {method} {endpoint} - {str(e)[:50]}")
        return False

def main():
    print("🔍 VibeCheck API Smoke Test")
    print("=" * 50)
    
    results = []
    
    # Health check
    print("\n🏥 Health Check")
    results.append(check("/health"))
    
    # Content endpoints (should work without auth)
    print("\n📚 Content Endpoints")
    results.append(check("/content/movies?limit=1"))
    results.append(check("/content/albums?limit=1"))
    results.append(check("/content/games?limit=1"))
    results.append(check("/content/books?limit=1"))
    results.append(check("/content/locations?limit=1"))
    
    # Search
    print("\n🔍 Search")
    results.append(check("/search?query=test&limit=1"))
    
    # Auth endpoints
    print("\n🔐 Auth (expect 400/401 without valid data)")
    check("/auth/login", "POST", json={"email": "test@test.com", "password": "wrong"})
    
    # Summary
    print("\n" + "=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} passed ({passed/total*100:.0f}%)")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
