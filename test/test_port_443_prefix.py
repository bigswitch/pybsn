"""Tests for port 443 with /sys prefix support

These include:
1. Port 443 with /sys prefix discovery
2. Fallback behavior when port 443 is unavailable
3. Prefix is correctly applied only to port 443
"""
import unittest
from unittest.mock import Mock, patch

import requests
import responses

import pybsn


class TestGuessUrlFallback(unittest.TestCase):
    """Test the guess_url() function's port discovery and fallback logic."""

    @responses.activate
    def test_port_443_with_sys_prefix_tried_first(self):
        """Port 443 with /sys prefix should be tried first."""
        responses.add(
            responses.GET,
            "https://10.0.0.1:443/sys/api/v1/auth/healthy",
            status=200,
            body="true"
        )

        session = requests.Session()
        url = pybsn.guess_url(session, "10.0.0.1")

        self.assertEqual(url, "https://10.0.0.1:443/sys")
        self.assertEqual(len(responses.calls), 1)

    @responses.activate
    def test_fallback_to_8443_when_443_unavailable(self):
        """Should fallback to port 8443 when 443 is not available."""
        responses.add(
            responses.GET,
            "https://10.0.0.1:443/sys/api/v1/auth/healthy",
            body=requests.exceptions.ConnectionError("Connection refused")
        )
        responses.add(
            responses.GET,
            "https://10.0.0.1:8443/api/v1/auth/healthy",
            status=200,
            body="true"
        )

        session = requests.Session()
        url = pybsn.guess_url(session, "10.0.0.1")

        self.assertEqual(url, "https://10.0.0.1:8443")
        self.assertEqual(len(responses.calls), 2)

    @responses.activate
    def test_fallback_to_8080_when_443_and_8443_unavailable(self):
        """Should fallback to port 8080 when both 443 and 8443 fail."""
        responses.add(
            responses.GET,
            "https://10.0.0.1:443/sys/api/v1/auth/healthy",
            body=requests.exceptions.ConnectionError("Connection refused")
        )
        responses.add(
            responses.GET,
            "https://10.0.0.1:8443/api/v1/auth/healthy",
            body=requests.exceptions.ConnectionError("Connection refused")
        )
        responses.add(
            responses.GET,
            "http://10.0.0.1:8080/api/v1/auth/healthy",
            status=200,
            body="true"
        )

        session = requests.Session()
        url = pybsn.guess_url(session, "10.0.0.1")

        self.assertEqual(url, "http://10.0.0.1:8080")
        self.assertEqual(len(responses.calls), 3)

    @responses.activate
    def test_non_200_response_causes_fallback(self):
        """Non-200 responses should cause fallback to next port."""
        responses.add(
            responses.GET,
            "https://10.0.0.1:443/sys/api/v1/auth/healthy",
            status=404
        )
        responses.add(
            responses.GET,
            "https://10.0.0.1:8443/api/v1/auth/healthy",
            status=200,
            body="true"
        )

        session = requests.Session()
        url = pybsn.guess_url(session, "10.0.0.1")

        self.assertEqual(url, "https://10.0.0.1:8443")

    @responses.activate
    def test_exception_when_all_ports_fail(self):
        """Should raise exception when all ports fail."""
        responses.add(
            responses.GET,
            "https://10.0.0.1:443/sys/api/v1/auth/healthy",
            body=requests.exceptions.ConnectionError("Connection refused")
        )
        responses.add(
            responses.GET,
            "https://10.0.0.1:8443/api/v1/auth/healthy",
            body=requests.exceptions.ConnectionError("Connection refused")
        )
        responses.add(
            responses.GET,
            "http://10.0.0.1:8080/api/v1/auth/healthy",
            body=requests.exceptions.ConnectionError("Connection refused")
        )

        session = requests.Session()
        with self.assertRaises(Exception) as context:
            pybsn.guess_url(session, "10.0.0.1")

        self.assertIn("Could not find available BigDB service", str(context.exception))

    @responses.activate
    def test_complete_url_bypasses_discovery(self):
        """Complete URLs should be returned as-is without port probing."""
        session = requests.Session()

        url = pybsn.guess_url(session, "https://10.0.0.1:8443")
        self.assertEqual(url, "https://10.0.0.1:8443")
        self.assertEqual(len(responses.calls), 0)


class TestPort443PrefixApplication(unittest.TestCase):
    """Test that /sys prefix is correctly applied only to port 443."""

    @responses.activate
    def test_sys_prefix_applied_to_port_443(self):
        """The /sys prefix should be included in all requests to port 443."""
        responses.add(
            responses.GET,
            "https://10.0.0.1:443/sys/api/v1/auth/healthy",
            status=200,
            body="true"
        )
        responses.add(
            responses.GET,
            "https://10.0.0.1:443/sys/api/v1/data/controller/core/switch",
            json=[{"dpid": "00:00:00:00:00:00:00:01"}],
            status=200
        )

        client = pybsn.connect("10.0.0.1")
        client.get("controller/core/switch")

        # Verify data request includes /sys prefix
        data_call = [c for c in responses.calls if "/data/" in c.request.url][0]
        self.assertIn("/sys/api/v1/data/", data_call.request.url)

    @responses.activate
    def test_sys_prefix_not_applied_to_port_8443(self):
        """The /sys prefix should NOT be included in requests to port 8443."""
        responses.add(
            responses.GET,
            "https://10.0.0.1:443/sys/api/v1/auth/healthy",
            body=requests.exceptions.ConnectionError("Connection refused")
        )
        responses.add(
            responses.GET,
            "https://10.0.0.1:8443/api/v1/auth/healthy",
            status=200,
            body="true"
        )
        responses.add(
            responses.GET,
            "https://10.0.0.1:8443/api/v1/data/controller/core/switch",
            json=[{"dpid": "00:00:00:00:00:00:00:01"}],
            status=200
        )

        client = pybsn.connect("10.0.0.1")
        client.get("controller/core/switch")

        # Verify data request does NOT include /sys prefix
        data_call = [c for c in responses.calls if "/data/" in c.request.url][0]
        self.assertNotIn("/sys", data_call.request.url)
        self.assertEqual(data_call.request.url, "https://10.0.0.1:8443/api/v1/data/controller/core/switch")

    @responses.activate
    def test_sys_prefix_not_applied_to_port_8080(self):
        """The /sys prefix should NOT be included in requests to port 8080."""
        responses.add(
            responses.GET,
            "https://10.0.0.1:443/sys/api/v1/auth/healthy",
            body=requests.exceptions.ConnectionError("Connection refused")
        )
        responses.add(
            responses.GET,
            "https://10.0.0.1:8443/api/v1/auth/healthy",
            body=requests.exceptions.ConnectionError("Connection refused")
        )
        responses.add(
            responses.GET,
            "http://10.0.0.1:8080/api/v1/auth/healthy",
            status=200,
            body="true"
        )
        responses.add(
            responses.GET,
            "http://10.0.0.1:8080/api/v1/data/controller/core/switch",
            json=[{"dpid": "00:00:00:00:00:00:00:01"}],
            status=200
        )

        client = pybsn.connect("10.0.0.1")
        client.get("controller/core/switch")

        # Verify data request does NOT include /sys prefix
        data_call = [c for c in responses.calls if "/data/" in c.request.url][0]
        self.assertNotIn("/sys", data_call.request.url)
        self.assertEqual(data_call.request.url, "http://10.0.0.1:8080/api/v1/data/controller/core/switch")

    @responses.activate
    def test_all_request_types_include_prefix_on_443(self):
        """All request types (data, rpc, schema) should include /sys prefix on port 443."""
        responses.add(
            responses.GET,
            "https://10.0.0.1:443/sys/api/v1/auth/healthy",
            status=200,
            body="true"
        )
        responses.add(
            responses.GET,
            "https://10.0.0.1:443/sys/api/v1/data/controller/core/switch",
            json=[],
            status=200
        )
        responses.add(
            responses.POST,
            "https://10.0.0.1:443/sys/api/v1/rpc/controller/test/action",
            json={"result": "ok"},
            status=200
        )
        responses.add(
            responses.GET,
            "https://10.0.0.1:443/sys/api/v1/schema/controller/core/switch",
            json={"type": "object"},
            status=200
        )

        client = pybsn.connect("10.0.0.1")
        client.get("controller/core/switch")
        client.rpc("controller/test/action", {})
        client.schema("controller/core/switch")

        # Verify all requests include /sys prefix
        for call in responses.calls[1:]:  # Skip the healthy check
            self.assertIn("/sys/api/v1/", call.request.url,
                         f"Request {call.request.url} should include /sys prefix")


class TestFallbackTiming(unittest.TestCase):
    """Test fallback timeout behavior."""

    def test_timeout_is_2_seconds(self):
        """Verify the timeout for each port probe is 2 seconds."""
        session = requests.Session()

        with patch.object(session, 'get') as mock_get:
            mock_get.side_effect = [
                Mock(status_code=404),
                Mock(status_code=200),
            ]

            pybsn.guess_url(session, "10.0.0.1")

            # Each call should have timeout=2
            for call in mock_get.call_args_list:
                self.assertEqual(call[1].get('timeout'), 2)

    def test_fallback_order_is_correct(self):
        """Verify ports are tried in order: 443, 8443, 8080."""
        session = requests.Session()

        with patch.object(session, 'get') as mock_get:
            mock_get.side_effect = [
                Mock(status_code=404),  # 443 fails
                Mock(status_code=404),  # 8443 fails
                Mock(status_code=200),  # 8080 succeeds
            ]

            pybsn.guess_url(session, "10.0.0.1")

            # Extract URLs from calls
            urls = [call[0][0] for call in mock_get.call_args_list]

            self.assertIn("443", urls[0], "First attempt should be port 443")
            self.assertIn("/sys", urls[0], "Port 443 should include /sys prefix")
            self.assertIn("8443", urls[1], "Second attempt should be port 8443")
            self.assertNotIn("/sys", urls[1], "Port 8443 should NOT include /sys prefix")
            self.assertIn("8080", urls[2], "Third attempt should be port 8080")


if __name__ == '__main__':
    unittest.main()
