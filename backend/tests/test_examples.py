"""
Example: How to use the VibeCheck API tester programmatically

This shows various ways to use the test suite for custom scenarios
"""

from test_api import VibeCheckAPITester
import json


def example_basic_usage():
    """Basic usage: Test all endpoints"""
    print("=" * 70)
    print("Example 1: Basic Full Test Suite")
    print("=" * 70)
    
    tester = VibeCheckAPITester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed. Check output above.")
    
    return success


def example_specific_tests():
    """Run only specific test categories"""
    print("\n" + "=" * 70)
    print("Example 2: Testing Specific Categories")
    print("=" * 70)
    
    tester = VibeCheckAPITester()
    
    print("\n📋 Testing Auth & Profile...")
    tester.test_register()
    tester.test_login()
    tester.test_get_profile()
    tester.test_update_profile()
    
    print("\n📋 Testing Content Discovery...")
    tester.test_get_movies()
    tester.test_get_albums()
    tester.test_get_games()
    tester.test_get_books()
    tester.test_get_locations()
    
    print("\n📋 Testing Aura Features...")
    tester.test_get_current_user_aura()
    tester.test_create_share()
    tester.test_get_user_shares()


def example_custom_workflow():
    """Simulate a real user workflow"""
    print("\n" + "=" * 70)
    print("Example 3: Simulating User Journey")
    print("=" * 70)
    
    tester = VibeCheckAPITester()
    
    print("\n👤 Step 1: User Registration & Login")
    if not tester.test_register():
        print("Failed to register user")
        return False
    
    if not tester.test_login():
        print("Failed to login")
        return False
    
    if tester.token:
        print(f"✓ Logged in with token: {tester.token[:20]}...")
    else:
        print("✓ Logged in (no token returned)")
    
    print("\n🎬 Step 2: Browsing Movies")
    tester.test_get_movies()
    tester.test_get_movies_with_search()
    
    print("\n📤 Step 3: Sharing Content")
    if not tester.test_create_share():
        print("Failed to create share")
        return False
    
    print("\n✨ Step 4: Viewing Aura Profile")
    tester.test_get_current_user_aura()
    tester.test_update_aura_profile()
    
    print("\n📊 Step 5: Checking Shares")
    tester.test_get_user_shares()
    
    print("\n✅ User journey completed successfully!")
    return True


def example_custom_url():
    """Test against a different environment"""
    print("\n" + "=" * 70)
    print("Example 4: Testing Different Environments")
    print("=" * 70)
    
    # Test local development
    print("\n🏠 Testing Local Development...")
    local_tester = VibeCheckAPITester(base_url="http://localhost:3000/api/v1")
    local_tester.test_health()
    
    # Test staging (example)
    # print("\n🔧 Testing Staging...")
    # staging_tester = VibeCheckAPITester(base_url="https://staging-api.vibecheck.com/api/v1")
    # staging_tester.test_health()
    
    # Test production (example)
    # print("\n🚀 Testing Production...")
    # prod_tester = VibeCheckAPITester(base_url="https://api.vibecheck.com/api/v1")
    # prod_tester.test_health()


def example_test_results_analysis():
    """Analyze test results programmatically"""
    print("\n" + "=" * 70)
    print("Example 5: Analyzing Test Results")
    print("=" * 70)
    
    tester = VibeCheckAPITester()
    
    # Run some tests
    tester.test_health()
    tester.test_register()
    tester.test_login()
    tester.test_get_movies()
    tester.test_get_albums()
    tester.test_get_games()
    
    # Analyze results
    total = len(tester.test_results)
    passed = sum(1 for r in tester.test_results if r['passed'])
    failed = total - passed
    
    print(f"\n📊 Test Statistics:")
    print(f"   Total: {total}")
    print(f"   Passed: {passed}")
    print(f"   Failed: {failed}")
    print(f"   Success Rate: {(passed/total*100):.1f}%")
    
    # Group by status code
    status_codes = {}
    for result in tester.test_results:
        code = result.get('status_code', 'N/A')
        status_codes[code] = status_codes.get(code, 0) + 1
    
    print(f"\n📈 Response Status Codes:")
    for code, count in sorted(status_codes.items()):
        print(f"   {code}: {count} tests")
    
    # Export results to JSON
    with open('test_results.json', 'w') as f:
        json.dump(tester.test_results, f, indent=2)
    print(f"\n💾 Results exported to: test_results.json")


def example_error_handling():
    """Demonstrate error handling"""
    print("\n" + "=" * 70)
    print("Example 6: Error Handling")
    print("=" * 70)
    
    # Test with invalid URL (should fail gracefully)
    print("\n🔴 Testing with invalid URL...")
    bad_tester = VibeCheckAPITester(base_url="http://localhost:9999/api/v1")
    bad_tester.test_health()  # Should log error gracefully
    
    # Test without authentication
    print("\n🔐 Testing endpoints that require auth (without token)...")
    no_auth_tester = VibeCheckAPITester()
    no_auth_tester.test_get_profile()  # Should fail with appropriate message


def example_performance_monitoring():
    """Monitor API performance"""
    print("\n" + "=" * 70)
    print("Example 7: Performance Monitoring")
    print("=" * 70)
    
    import time
    
    tester = VibeCheckAPITester()
    
    endpoints = [
        ("GET /content/movies", lambda: tester.test_get_movies()),
        ("GET /content/albums", lambda: tester.test_get_albums()),
        ("GET /content/games", lambda: tester.test_get_games()),
        ("GET /content/books", lambda: tester.test_get_books()),
        ("GET /content/locations", lambda: tester.test_get_locations()),
    ]
    
    print("\n⏱️  Measuring response times...")
    
    for name, test_func in endpoints:
        start = time.time()
        test_func()
        duration = time.time() - start
        print(f"   {name}: {duration*1000:.0f}ms")


def example_data_validation():
    """Validate response data structures"""
    print("\n" + "=" * 70)
    print("Example 8: Response Data Validation")
    print("=" * 70)
    
    import requests
    
    tester = VibeCheckAPITester()
    
    # Test movies response structure
    print("\n🔍 Validating Movies Response Structure...")
    response = requests.get(f"{tester.base_url}/content/movies?limit=1")
    if response.status_code == 200:
        data = response.json()
        
        # Check expected fields
        if 'items' in data:
            print("   ✓ Has 'items' field")
            if len(data['items']) > 0:
                movie = data['items'][0]
                expected_fields = ['id', 'title', 'year', 'director', 'type']
                for field in expected_fields:
                    if field in movie:
                        print(f"   ✓ Movie has '{field}' field")
                    else:
                        print(f"   ✗ Movie missing '{field}' field")
        
        if 'total' in data:
            print(f"   ✓ Has 'total' field: {data['total']}")


# ─────────────────────────────────────────────────────────
# MAIN EXECUTION
# ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    
    examples = {
        '1': ('Basic Full Test Suite', example_basic_usage),
        '2': ('Testing Specific Categories', example_specific_tests),
        '3': ('Simulating User Journey', example_custom_workflow),
        '4': ('Testing Different Environments', example_custom_url),
        '5': ('Analyzing Test Results', example_test_results_analysis),
        '6': ('Error Handling', example_error_handling),
        '7': ('Performance Monitoring', example_performance_monitoring),
        '8': ('Response Data Validation', example_data_validation),
    }
    
    if len(sys.argv) > 1:
        # Run specific example
        example_num = sys.argv[1]
        if example_num in examples:
            name, func = examples[example_num]
            print(f"\n🎯 Running Example {example_num}: {name}\n")
            func()
        else:
            print(f"Unknown example: {example_num}")
            print(f"Available examples: {', '.join(examples.keys())}")
    else:
        # Show menu
        print("\n" + "=" * 70)
        print("VibeCheck API Test Examples")
        print("=" * 70)
        print("\nAvailable examples:")
        for num, (name, _) in examples.items():
            print(f"  {num}. {name}")
        print("\nUsage:")
        print(f"  python {sys.argv[0]} <example_number>")
        print(f"\nExample:")
        print(f"  python {sys.argv[0]} 3")
        print("\n" + "=" * 70)
