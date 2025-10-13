#!/usr/bin/env python
"""
Real integration test with actual HTTP server to validate retry behavior.

This test uses a real HTTP server on an ephemeral port to verify that:
1. GET requests ARE retried on connection failures
2. POST requests are NOT retried on connection failures (even with retries=3)
3. PATCH requests are NOT retried on connection failures (even with retries=3)
"""
import http.server
import json
import socketserver
import threading
import time
import unittest

import requests

import pybsn


class RequestCountingHandler(http.server.BaseHTTPRequestHandler):
    """HTTP handler that tracks request counts"""

    # Class variables to track requests
    get_count = 0
    post_count = 0
    patch_count = 0
    fail_first_n_gets = 0  # Fail first N GET requests by closing connection

    @classmethod
    def reset_counts(cls):
        cls.get_count = 0
        cls.post_count = 0
        cls.patch_count = 0
        cls.fail_first_n_gets = 0

    def log_message(self, format, *args):
        """Suppress server logs during tests"""
        pass

    def do_GET(self):
        RequestCountingHandler.get_count += 1

        # Fail first N GETs by closing connection (simulates connection error)
        if RequestCountingHandler.get_count <= RequestCountingHandler.fail_first_n_gets:
            # Close connection without sending response
            self.wfile.close()
            return

        # Successful response
        if "/api/v1/auth/healthy" in self.path:
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(b"{}")
        elif "/api/v1/data/controller/core/switch" in self.path:
            result = [{"name": "switch1"}]
            response = json.dumps(result).encode()
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Content-length", str(len(response)))
            self.end_headers()
            self.wfile.write(response)

    def do_POST(self):
        RequestCountingHandler.post_count += 1

        # Close connection immediately (simulate connection error)
        # This tests that POST is NOT retried
        if "/api/v1/data/controller/core/switch" in self.path:
            self.wfile.close()
            return

        # Login endpoint
        if "/api/v1/rpc/controller/core/aaa/session/login" in self.path:
            result = {
                "success": True,
                "session-cookie": "test-cookie",
                "error-message": "",
            }
            response = json.dumps(result).encode()
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Content-length", str(len(response)))
            self.end_headers()
            self.wfile.write(response)

    def do_PATCH(self):
        RequestCountingHandler.patch_count += 1

        # Close connection immediately (simulate connection error)
        # This tests that PATCH is NOT retried
        self.wfile.close()


class TestRetryRealServer(unittest.TestCase):
    """Test retry behavior with real HTTP server"""

    @classmethod
    def setUpClass(cls):
        """Start HTTP server on ephemeral port"""
        # Use port 0 for automatic ephemeral port assignment
        cls.server = socketserver.TCPServer(("127.0.0.1", 0), RequestCountingHandler)
        cls.port = cls.server.server_address[1]
        cls.url = f"http://127.0.0.1:{cls.port}"

        # Start server in background thread
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()

        # Give server time to start
        time.sleep(0.1)

    @classmethod
    def tearDownClass(cls):
        """Stop HTTP server"""
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        """Reset request counts before each test"""
        RequestCountingHandler.reset_counts()

    def test_retry_int_does_retry_get_on_real_connection_error(self):
        """
        Real test: GET requests ARE retried on connection errors with retries=3.

        This uses a real HTTP server that drops connections to verify urllib3 retry behavior.
        """
        # Configure server to fail first 2 GETs by closing connection
        RequestCountingHandler.fail_first_n_gets = 2

        # Connect with retries=3
        client = pybsn.connect(self.url, "admin", "password", retries=3)

        # This should succeed after 2 retries (3rd attempt succeeds)
        result = client.get("controller/core/switch")

        # Verify we got the result
        self.assertEqual(result, [{"name": "switch1"}])

        # Verify 3 GET requests were made to /switch (2 failures + 1 success)
        # Note: Additional GETs to /healthy during connection setup
        self.assertGreaterEqual(
            RequestCountingHandler.get_count,
            3,
            "Should have made at least 3 GET requests (2 failed + 1 success)",
        )

    def test_retry_int_does_not_retry_post_on_real_connection_error(self):
        """
        Real test: POST requests are NOT retried on connection errors with retries=3.

        This uses a real HTTP server that drops POST connections to verify urllib3 does NOT retry.
        """
        # Connect with retries=3
        client = pybsn.connect(self.url, "admin", "password", retries=3)

        # POST that gets connection closed should NOT be retried
        with self.assertRaises(Exception):  # Connection error or similar
            client.post("controller/core/switch", data={"name": "test"})

        # Verify only 1 POST request was made (no retries)
        # Note: +1 for login POST
        self.assertEqual(
            RequestCountingHandler.post_count,
            2,  # 1 login + 1 failed POST
            "Should only make 1 POST request to /switch (no retries)",
        )

    def test_retry_int_does_not_retry_patch_on_real_connection_error(self):
        """
        Real test: PATCH requests are NOT retried on connection errors with retries=3.

        This uses a real HTTP server that drops PATCH connections to verify urllib3 does NOT retry.
        """
        # Connect with retries=3
        client = pybsn.connect(self.url, "admin", "password", retries=3)

        # PATCH that gets connection closed should NOT be retried
        with self.assertRaises(Exception):  # Connection error or similar
            client.patch("controller/core/switch", data={"name": "test"})

        # Verify only 1 PATCH request was made (no retries)
        self.assertEqual(RequestCountingHandler.patch_count, 1, "Should only make 1 PATCH request (no retries)")


if __name__ == "__main__":
    unittest.main()
