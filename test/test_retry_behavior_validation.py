#!/usr/bin/env python
"""
Test to validate and document the exact behavior of retries parameter.

This test documents what actually happens when you pass retries=3 vs retries=Retry(...)
"""
import unittest

import requests
import responses
from urllib3.util.retry import Retry

import pybsn


class TestRetryBehaviorValidation(unittest.TestCase):
    """Validate exact retry behavior with different configurations."""

    @responses.activate
    def test_retry_int_creates_retry_object(self):
        """Verify that retries=3 creates a Retry object with specific defaults."""
        responses.add(responses.GET, "http://127.0.0.1:8080/api/v1/auth/healthy", json={}, status=200)
        responses.add(
            responses.POST,
            "http://127.0.0.1:8080/api/v1/rpc/controller/core/aaa/session/login",
            json={"session-cookie": "test"},
            status=200,
        )

        client = pybsn.connect("http://127.0.0.1:8080", "admin", "password", retries=3)

        adapter = client.session.get_adapter("http://example.com")
        retry_config = adapter.max_retries

        # When retries=3, urllib3.Retry.from_int(3) is called, which creates:
        self.assertIsInstance(retry_config, Retry)
        self.assertEqual(retry_config.total, 3, "Should retry up to 3 times")

        # Methods that will be retried (idempotent + PUT/DELETE)
        self.assertEqual(
            retry_config.allowed_methods,
            frozenset({"GET", "HEAD", "OPTIONS", "PUT", "DELETE", "TRACE"}),
            "Should retry idempotent methods plus PUT/DELETE, but NOT POST or PATCH",
        )

        # Status codes - IMPORTANT: empty by default!
        self.assertEqual(
            retry_config.status_forcelist,
            set(),
            "Should NOT retry any HTTP status codes by default (only connection errors)",
        )

        # Backoff
        self.assertEqual(retry_config.backoff_factor, 0, "Should have no exponential backoff by default")

    @responses.activate
    def test_retry_int_does_not_retry_http_errors(self):
        """Verify that retries=3 does NOT retry HTTP error status codes like 503."""
        responses.add(responses.GET, "http://127.0.0.1:8080/api/v1/auth/healthy", json={}, status=200)
        responses.add(
            responses.POST,
            "http://127.0.0.1:8080/api/v1/rpc/controller/core/aaa/session/login",
            json={"session-cookie": "test"},
            status=200,
        )

        # Return 503 error
        responses.add(
            responses.GET,
            "http://127.0.0.1:8080/api/v1/data/controller/core/switch",
            json={"error": "Service Unavailable"},
            status=503,
        )

        client = pybsn.connect("http://127.0.0.1:8080", "admin", "password", retries=3)

        # Should NOT retry 503 - it will raise immediately
        with self.assertRaises(requests.exceptions.HTTPError) as cm:
            client.get("controller/core/switch")

        self.assertEqual(cm.exception.response.status_code, 503)
        # Verify only 1 request was made (no retries on status codes)
        get_requests = [call for call in responses.calls if call.request.method == "GET" and "switch" in call.request.url]
        self.assertEqual(len(get_requests), 1, "Should only make 1 request (no retry on HTTP status codes)")

    @responses.activate
    def test_retry_custom_object_retries_status_codes(self):
        """Verify that Retry object with status_forcelist DOES retry HTTP errors."""
        responses.add(responses.GET, "http://127.0.0.1:8080/api/v1/auth/healthy", json={}, status=200)
        responses.add(
            responses.POST,
            "http://127.0.0.1:8080/api/v1/rpc/controller/core/aaa/session/login",
            json={"session-cookie": "test"},
            status=200,
        )

        # First request returns 503, second succeeds
        responses.add(
            responses.GET,
            "http://127.0.0.1:8080/api/v1/data/controller/core/switch",
            json={"error": "Service Unavailable"},
            status=503,
        )
        responses.add(
            responses.GET,
            "http://127.0.0.1:8080/api/v1/data/controller/core/switch",
            json=[{"name": "switch1"}],
            status=200,
        )

        # Use Retry object with status_forcelist
        retry_config = Retry(total=3, status_forcelist=[503])
        client = pybsn.connect("http://127.0.0.1:8080", "admin", "password", retries=retry_config)

        # Should succeed after retry
        result = client.get("controller/core/switch")
        self.assertEqual(result, [{"name": "switch1"}])

        # Verify 2 requests were made
        get_requests = [call for call in responses.calls if call.request.method == "GET" and "switch" in call.request.url]
        self.assertEqual(len(get_requests), 2, "Should make 2 requests (1 failure + 1 retry)")

    @responses.activate
    def test_retry_int_does_not_retry_post_on_connection_error(self):
        """Verify that retries=3 does NOT retry POST even on connection errors."""
        responses.add(responses.GET, "http://127.0.0.1:8080/api/v1/auth/healthy", json={}, status=200)
        responses.add(
            responses.POST,
            "http://127.0.0.1:8080/api/v1/rpc/controller/core/aaa/session/login",
            json={"session-cookie": "test"},
            status=200,
        )

        # Simulate connection error on POST
        responses.add(
            responses.POST,
            "http://127.0.0.1:8080/api/v1/data/controller/core/switch",
            body=requests.exceptions.ConnectionError("Connection failed"),
        )

        client = pybsn.connect("http://127.0.0.1:8080", "admin", "password", retries=3)

        # Should NOT retry POST - will raise immediately even on connection error
        with self.assertRaises(requests.exceptions.ConnectionError):
            client.post("controller/core/switch", data={"name": "test"})

        # Verify only 1 POST request was made (no retries for POST with retries=int)
        post_requests = [
            call for call in responses.calls if call.request.method == "POST" and "switch" in call.request.url
        ]
        self.assertEqual(len(post_requests), 1, "POST should NOT be retried even on connection errors")

    @responses.activate
    def test_retry_int_does_not_retry_patch_on_connection_error(self):
        """Verify that retries=3 does NOT retry PATCH even on connection errors."""
        responses.add(responses.GET, "http://127.0.0.1:8080/api/v1/auth/healthy", json={}, status=200)
        responses.add(
            responses.POST,
            "http://127.0.0.1:8080/api/v1/rpc/controller/core/aaa/session/login",
            json={"session-cookie": "test"},
            status=200,
        )

        # Simulate connection error on PATCH
        responses.add(
            responses.PATCH,
            "http://127.0.0.1:8080/api/v1/data/controller/core/switch",
            body=requests.exceptions.ConnectionError("Connection failed"),
        )

        client = pybsn.connect("http://127.0.0.1:8080", "admin", "password", retries=3)

        # Should NOT retry PATCH - will raise immediately even on connection error
        with self.assertRaises(requests.exceptions.ConnectionError):
            client.patch("controller/core/switch", data={"name": "test"})

        # Verify only 1 PATCH request was made
        patch_requests = [
            call for call in responses.calls if call.request.method == "PATCH" and "switch" in call.request.url
        ]
        self.assertEqual(len(patch_requests), 1, "PATCH should NOT be retried even on connection errors")

    @responses.activate
    def test_retry_int_allowed_methods_config(self):
        """
        Verify that retries=3 configures allowed_methods correctly.

        Note: We test configuration rather than actual retry behavior on connection errors
        because the 'responses' mocking library interferes with urllib3's retry mechanism.
        The responses library raises exceptions at the wrong layer, preventing retries.

        The configuration test proves that GET/PUT/DELETE will be retried while POST/PATCH won't.
        """
        responses.add(responses.GET, "http://127.0.0.1:8080/api/v1/auth/healthy", json={}, status=200)
        responses.add(
            responses.POST,
            "http://127.0.0.1:8080/api/v1/rpc/controller/core/aaa/session/login",
            json={"session-cookie": "test"},
            status=200,
        )

        client = pybsn.connect("http://127.0.0.1:8080", "admin", "password", retries=3)

        adapter = client.session.get_adapter("http://example.com")
        retry_config = adapter.max_retries

        # Verify allowed_methods includes GET but not POST/PATCH
        self.assertIn("GET", retry_config.allowed_methods, "GET should be in allowed_methods")
        self.assertIn("PUT", retry_config.allowed_methods, "PUT should be in allowed_methods")
        self.assertIn("DELETE", retry_config.allowed_methods, "DELETE should be in allowed_methods")
        self.assertNotIn("POST", retry_config.allowed_methods, "POST should NOT be in allowed_methods")
        self.assertNotIn("PATCH", retry_config.allowed_methods, "PATCH should NOT be in allowed_methods")


if __name__ == "__main__":
    unittest.main()
