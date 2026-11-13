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

        # Methods eligible for read/status retries (connect failures apply to all methods).
        self.assertEqual(
            retry_config.allowed_methods,
            frozenset({"GET", "HEAD", "OPTIONS", "PUT", "DELETE", "TRACE"}),
            "Read/status retries should exclude POST and PATCH",
        )

        # Status codes - IMPORTANT: empty by default!
        self.assertEqual(
            retry_config.status_forcelist,
            set(),
            "No forced HTTP status codes; Retry-After handling remains enabled",
        )

        # Backoff
        self.assertEqual(retry_config.backoff_factor, 0, "Should have no exponential backoff by default")

    @responses.activate
    def test_retry_int_does_not_retry_503_without_retry_after(self):
        """An integer retry count does not retry 503 without Retry-After."""
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


if __name__ == "__main__":
    unittest.main()
