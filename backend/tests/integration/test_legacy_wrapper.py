import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(__file__))
from test_api import VibeCheckAPITester

@pytest.mark.integration
def test_legacy_api_endpoints():
    """
    Unified test wrapper for all legacy API endpoints.
    This integrates the comprehensive 125KB test_api.py suite into pytest.
    """
    tester = VibeCheckAPITester(base_url="http://localhost:3000/api/v1")
    success = tester.run_all_tests()
    
    # tester.run_all_tests() returns True if all tests pass, False otherwise.
    assert success is True, "Legacy API tests failed. Check console output for details."
