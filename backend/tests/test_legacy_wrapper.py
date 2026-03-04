import os
import sys
import pytest
import socket

sys.path.insert(0, os.path.dirname(__file__))
from test_api import VibeCheckAPITester


def _is_backend_available(host: str = "localhost", port: int = 3000, timeout: float = 1.0) -> bool:
    """
    Lightweight availability check for the legacy backend.
    Returns True if a TCP connection to the given host/port can be established.
    """
    try:
        with socket.create_connection((host, port), timeout):
            return True
    except OSError:
        return False


def test_legacy_api_endpoints():
    """
    Unified test wrapper for all legacy API endpoints.
    This integrates the comprehensive 125KB test_api.py suite into pytest.
    """
    if not _is_backend_available():
        pytest.skip(
            "Legacy API backend not running on http://localhost:3000; skipping integration test."
        )
    tester = VibeCheckAPITester(base_url="http://localhost:3000/api/v1")
    success = tester.run_all_tests()
    
    # tester.run_all_tests() returns True if all tests pass, False otherwise.
    assert success is True, "Legacy API tests failed. Check console output for details."
