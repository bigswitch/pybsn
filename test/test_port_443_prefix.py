"""Tests for port 443 with /a prefix support

These include:
1. Port 443 with /a prefix discovery
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
    def test_port_443_with_prefix_tried_first(self):
        """Port 443 with /a prefix should be tried first."""
        responses.add(responses.GET, "https://192.0.2.1:443/a/api/v1/auth/healthy", status=200, body="true")

        session = requests.Session()
        url = pybsn.guess_url(session, "192.0.2.1")

        self.assertEqual(url, "https://192.0.2.1:443/a")
        self.assertEqual(len(responses.calls), 1)

    @responses.activate
    def test_fallback_to_8443_when_443_unavailable(self):
        """Should fallback to port 8443 when 443 is not available."""
        responses.add(
            responses.GET,
            "https://192.0.2.1:443/a/api/v1/auth/healthy",
            body=requests.exceptions.ConnectionError("Connection refused"),
        )
        responses.add(responses.GET, "https://192.0.2.1:8443/api/v1/auth/healthy", status=200, body="true")

        session = requests.Session()
        url = pybsn.guess_url(session, "192.0.2.1")

        self.assertEqual(url, "https://192.0.2.1:8443")
        self.assertEqual(len(responses.calls), 2)

    @responses.activate
    def test_fallback_to_8080_when_443_and_8443_unavailable(self):
        """Should fallback to port 8080 when both 443 and 8443 fail."""
        responses.add(
            responses.GET,
            "https://192.0.2.1:443/a/api/v1/auth/healthy",
            body=requests.exceptions.ConnectionError("Connection refused"),
        )
        responses.add(
            responses.GET,
            "https://192.0.2.1:8443/api/v1/auth/healthy",
            body=requests.exceptions.ConnectionError("Connection refused"),
        )
        responses.add(responses.GET, "http://192.0.2.1:8080/api/v1/auth/healthy", status=200, body="true")

        session = requests.Session()
        url = pybsn.guess_url(session, "192.0.2.1")

        self.assertEqual(url, "http://192.0.2.1:8080")
        self.assertEqual(len(responses.calls), 3)

    @responses.activate
    def test_non_200_response_causes_fallback(self):
        """Non-200 responses should cause fallback to next port."""
        responses.add(responses.GET, "https://192.0.2.1:443/a/api/v1/auth/healthy", status=404)
        responses.add(responses.GET, "https://192.0.2.1:8443/api/v1/auth/healthy", status=200, body="true")

        session = requests.Session()
        url = pybsn.guess_url(session, "192.0.2.1")

        self.assertEqual(url, "https://192.0.2.1:8443")

    @responses.activate
    def test_exception_when_all_ports_fail(self):
        """Should raise exception when all ports fail."""
        responses.add(
            responses.GET,
            "https://192.0.2.1:443/a/api/v1/auth/healthy",
            body=requests.exceptions.ConnectionError("Connection refused"),
        )
        responses.add(
            responses.GET,
            "https://192.0.2.1:8443/api/v1/auth/healthy",
            body=requests.exceptions.ConnectionError("Connection refused"),
        )
        responses.add(
            responses.GET,
            "http://192.0.2.1:8080/api/v1/auth/healthy",
            body=requests.exceptions.ConnectionError("Connection refused"),
        )

        session = requests.Session()
        with self.assertRaises(Exception) as context:
            pybsn.guess_url(session, "192.0.2.1")

        self.assertIn("Could not find available BigDB service", str(context.exception))

    @responses.activate
    def test_complete_url_bypasses_discovery(self):
        """Complete URLs should be returned as-is without port probing."""
        session = requests.Session()

        url = pybsn.guess_url(session, "https://192.0.2.1:8443")
        self.assertEqual(url, "https://192.0.2.1:8443")
        self.assertEqual(len(responses.calls), 0)


class TestPort443PrefixApplication(unittest.TestCase):
    """Test that /a prefix is correctly applied only to port 443."""

    @responses.activate
    def test_prefix_applied_to_port_443(self):
        """The /a prefix should be included in all requests to port 443."""
        responses.add(responses.GET, "https://192.0.2.1:443/a/api/v1/auth/healthy", status=200, body="true")
        responses.add(
            responses.GET,
            "https://192.0.2.1:443/a/api/v1/data/controller/core/switch",
            json=[{"dpid": "00:00:00:00:00:00:00:01"}],
            status=200,
        )

        client = pybsn.connect("192.0.2.1")
        client.get("controller/core/switch")

        # Verify data request includes /a prefix
        data_call = [c for c in responses.calls if "/data/" in c.request.url][0]
        self.assertIn("/a/api/v1/data/", data_call.request.url)

    @responses.activate
    def test_prefix_not_applied_to_port_8443(self):
        """The /a prefix should NOT be included in requests to port 8443."""
        responses.add(
            responses.GET,
            "https://192.0.2.1:443/a/api/v1/auth/healthy",
            body=requests.exceptions.ConnectionError("Connection refused"),
        )
        responses.add(responses.GET, "https://192.0.2.1:8443/api/v1/auth/healthy", status=200, body="true")
        responses.add(
            responses.GET,
            "https://192.0.2.1:8443/api/v1/data/controller/core/switch",
            json=[{"dpid": "00:00:00:00:00:00:00:01"}],
            status=200,
        )

        client = pybsn.connect("192.0.2.1")
        client.get("controller/core/switch")

        # Verify data request does NOT include /a prefix
        data_call = [c for c in responses.calls if "/data/" in c.request.url][0]
        self.assertNotIn("/a/", data_call.request.url)
        self.assertEqual(data_call.request.url, "https://192.0.2.1:8443/api/v1/data/controller/core/switch")

    @responses.activate
    def test_prefix_not_applied_to_port_8080(self):
        """The /a prefix should NOT be included in requests to port 8080."""
        responses.add(
            responses.GET,
            "https://192.0.2.1:443/a/api/v1/auth/healthy",
            body=requests.exceptions.ConnectionError("Connection refused"),
        )
        responses.add(
            responses.GET,
            "https://192.0.2.1:8443/api/v1/auth/healthy",
            body=requests.exceptions.ConnectionError("Connection refused"),
        )
        responses.add(responses.GET, "http://192.0.2.1:8080/api/v1/auth/healthy", status=200, body="true")
        responses.add(
            responses.GET,
            "http://192.0.2.1:8080/api/v1/data/controller/core/switch",
            json=[{"dpid": "00:00:00:00:00:00:00:01"}],
            status=200,
        )

        client = pybsn.connect("192.0.2.1")
        client.get("controller/core/switch")

        # Verify data request does NOT include /a prefix
        data_call = [c for c in responses.calls if "/data/" in c.request.url][0]
        self.assertNotIn("/a/", data_call.request.url)
        self.assertEqual(data_call.request.url, "http://192.0.2.1:8080/api/v1/data/controller/core/switch")

    @responses.activate
    def test_all_request_types_include_prefix_on_443(self):
        """All request types (data, rpc, schema) should include /a prefix on port 443."""
        responses.add(responses.GET, "https://192.0.2.1:443/a/api/v1/auth/healthy", status=200, body="true")
        responses.add(responses.GET, "https://192.0.2.1:443/a/api/v1/data/controller/core/switch", json=[], status=200)
        responses.add(
            responses.POST, "https://192.0.2.1:443/a/api/v1/rpc/controller/test/action", json={"result": "ok"}, status=200
        )
        responses.add(
            responses.GET, "https://192.0.2.1:443/a/api/v1/schema/controller/core/switch", json={"type": "object"}, status=200
        )

        client = pybsn.connect("192.0.2.1")
        client.get("controller/core/switch")
        client.rpc("controller/test/action", {})
        client.schema("controller/core/switch")

        # Verify all requests include /a prefix
        for call in responses.calls[1:]:  # Skip the healthy check
            self.assertIn(
                "/a/api/v1/",
                call.request.url,
                f"Request {call.request.url} should include /a prefix",
            )


class TestSchemalessUrl(unittest.TestCase):
    """Test handling of schema-less URLs with explicit port or path prefix."""

    @responses.activate
    def test_explicit_port_uses_https(self):
        """host:8443 should use https and only probe that port."""
        responses.add(responses.GET, "https://192.0.2.1:8443/api/v1/auth/healthy", status=200, body="true")

        session = requests.Session()
        url = pybsn.guess_url(session, "192.0.2.1:8443")

        self.assertEqual(url, "https://192.0.2.1:8443")
        self.assertEqual(len(responses.calls), 1)

    @responses.activate
    def test_explicit_port_443_uses_https(self):
        """host:443 should use https and only probe that port."""
        responses.add(responses.GET, "https://192.0.2.1:443/a/api/v1/auth/healthy", status=200, body="true")

        session = requests.Session()
        url = pybsn.guess_url(session, "192.0.2.1:443/a")

        self.assertEqual(url, "https://192.0.2.1:443/a")
        self.assertEqual(len(responses.calls), 1)

    @responses.activate
    def test_explicit_port_8080_uses_http(self):
        """host:8080 should use http and only probe that port."""
        responses.add(responses.GET, "http://192.0.2.1:8080/api/v1/auth/healthy", status=200, body="true")

        session = requests.Session()
        url = pybsn.guess_url(session, "192.0.2.1:8080")

        self.assertEqual(url, "http://192.0.2.1:8080")
        self.assertEqual(len(responses.calls), 1)

    @responses.activate
    def test_custom_path_prefix_probes_all_ports(self):
        """host/custom-prefix should probe all ports with that prefix."""
        responses.add(
            responses.GET,
            "https://192.0.2.1:443/custom/api/v1/auth/healthy",
            body=requests.exceptions.ConnectionError("Connection refused"),
        )
        responses.add(responses.GET, "https://192.0.2.1:8443/custom/api/v1/auth/healthy", status=200, body="true")

        session = requests.Session()
        url = pybsn.guess_url(session, "192.0.2.1/custom")

        self.assertEqual(url, "https://192.0.2.1:8443/custom")
        self.assertEqual(len(responses.calls), 2)


class TestFallbackTiming(unittest.TestCase):
    """Test fallback timeout behavior."""

    def test_timeout_is_2_seconds(self):
        """Verify the timeout for each port probe is 2 seconds."""
        session = requests.Session()

        with patch.object(session, "get") as mock_get:
            mock_get.side_effect = [
                Mock(status_code=404),
                Mock(status_code=200),
            ]

            pybsn.guess_url(session, "192.0.2.1")

            # Each call should have timeout=2
            for call in mock_get.call_args_list:
                self.assertEqual(call[1].get("timeout"), 2)

    def test_fallback_order_is_correct(self):
        """Verify ports are tried in order: 443, 8443, 8080."""
        session = requests.Session()

        with patch.object(session, "get") as mock_get:
            mock_get.side_effect = [
                Mock(status_code=404),  # 443 fails
                Mock(status_code=404),  # 8443 fails
                Mock(status_code=200),  # 8080 succeeds
            ]

            pybsn.guess_url(session, "192.0.2.1")

            # Extract URLs from calls
            urls = [call[0][0] for call in mock_get.call_args_list]

            self.assertIn("443", urls[0], "First attempt should be port 443")
            self.assertIn(pybsn.API_PREFIX, urls[0], "Port 443 should include /a prefix")
            self.assertIn("8443", urls[1], "Second attempt should be port 8443")
            self.assertNotIn("/a/", urls[1], "Port 8443 should NOT include /a prefix")
            self.assertIn("8080", urls[2], "Third attempt should be port 8080")


if __name__ == "__main__":
    unittest.main()
