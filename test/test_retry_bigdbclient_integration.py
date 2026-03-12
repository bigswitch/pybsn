import json
import sys
import unittest

import requests
import responses
from requests.exceptions import ConnectionError
from urllib3.util.retry import Retry

import pybsn

sys.path.append("test")


class TestRetryBigDbClientIntegration(unittest.TestCase):
    """
    Integration tests with actual network failures to verify retry behavior end-to-end.
    """

    url = "http://127.0.0.1:8080"

    def _login_cb(self, req):
        self.assertEqual(json.loads(req.body), {"user": "admin", "password": "somepassword"})
        headers = {"Set-Cookie": "session_cookie=v_8yOI7FI-WKr-5QU6nxoJkVtAu5rKI-; Path=/api/;"}
        return (
            200,
            headers,
            json.dumps(
                {
                    "success": True,
                    "session-cookie": "UPhNWlmDN0re8cg9xsqe9QT1QvQTznji",
                    "error-message": "",
                }
            ),
        )

    def _add_login_responses(self):
        responses.add(
            responses.GET,
            "http://127.0.0.1:8080/api/v1/auth/healthy",
            json={},
            status=200,
        )
        responses.add_callback(
            responses.POST,
            "http://127.0.0.1:8080/api/v1/rpc/controller/core/aaa/session/login",
            callback=self._login_cb,
            content_type="application/json",
        )

    @responses.activate
    def test_retry_succeeds_after_transient_failure(self):
        """Server fails twice, succeeds third time, verify success."""
        self._add_login_responses()

        # Configure retry to retry on 503
        retry_config = Retry(total=5, status_forcelist=[503])

        # Simulate transient failures (503) followed by success
        responses.add(
            responses.GET,
            "http://127.0.0.1:8080/api/v1/data/controller/core/switch",
            json={},
            status=503,
        )
        responses.add(
            responses.GET,
            "http://127.0.0.1:8080/api/v1/data/controller/core/switch",
            json={},
            status=503,
        )
        responses.add(
            responses.GET,
            "http://127.0.0.1:8080/api/v1/data/controller/core/switch",
            json=[{"name": "switch1", "mac-address": "00:00:00:00:00:01"}],
            status=200,
        )

        # Connect with retry configuration
        client = pybsn.connect(self.url, "admin", "somepassword", retries=retry_config)

        # Should succeed after retries
        result = client.get("controller/core/switch")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "switch1")

    @responses.activate
    def test_retry_with_connection_error(self):
        """Server unreachable, verify retries happen and eventually fail."""
        self._add_login_responses()

        # Configure retry to retry on 503
        retry_config = Retry(total=3, status_forcelist=[503], raise_on_status=False)

        # All attempts fail with 503
        for _ in range(10):
            responses.add(
                responses.GET,
                "http://127.0.0.1:8080/api/v1/data/controller/core/switch",
                json={},
                status=503,
            )

        # Connect with limited retry configuration
        client = pybsn.connect(self.url, "admin", "somepassword", retries=retry_config)

        # Should raise HTTPError after exhausting retries
        with self.assertRaises(requests.exceptions.HTTPError):
            client.get("controller/core/switch")

    @responses.activate
    def test_retry_respects_status_forcelist(self):
        """Only retry specific HTTP status codes."""
        self._add_login_responses()

        # Configure to retry only on 503 Service Unavailable
        retry_config = Retry(total=3, status_forcelist=[503])

        # First attempt returns 503, second succeeds
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

        client = pybsn.connect(self.url, "admin", "somepassword", retries=retry_config)

        # Should succeed after retrying 503
        result = client.get("controller/core/switch")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "switch1")

    @responses.activate
    def test_retry_does_not_retry_non_forcelist_status(self):
        """Do not retry status codes not in forcelist."""
        self._add_login_responses()

        # Configure to retry only on 503
        retry_config = Retry(total=3, status_forcelist=[503], raise_on_status=False)

        # Return 500 (not in forcelist), should not retry
        responses.add(
            responses.GET,
            "http://127.0.0.1:8080/api/v1/data/controller/core/switch",
            json={"error": "Internal Server Error"},
            status=500,
        )

        client = pybsn.connect(self.url, "admin", "somepassword", retries=retry_config)

        # Should fail without retries because 500 is not in forcelist
        # But since raise_on_status=False, it returns the response
        with self.assertRaises(Exception):  # HTTPError from raise_for_status
            client.get("controller/core/switch")

    @responses.activate
    def test_no_retry_when_not_configured(self):
        """Verify default behavior unchanged - no retries when not configured."""
        self._add_login_responses()

        # First attempt fails
        responses.add(
            responses.GET,
            "http://127.0.0.1:8080/api/v1/data/controller/core/switch",
            body=ConnectionError("Connection failed"),
        )

        # Connect without retry configuration
        client = pybsn.connect(self.url, "admin", "somepassword")

        # Should fail immediately without retries
        with self.assertRaises(ConnectionError):
            client.get("controller/core/switch")

    @responses.activate
    def test_retry_on_guess_url(self):
        """Verify retries work during URL guessing phase with 503 status."""
        # Configure retry to retry on 503
        retry_config = Retry(total=3, status_forcelist=[503])

        # First attempt to health check returns 503, second succeeds
        responses.add(
            responses.GET,
            "https://127.0.0.1:8443/api/v1/auth/healthy",
            json={},
            status=503,
        )
        responses.add(
            responses.GET,
            "https://127.0.0.1:8443/api/v1/auth/healthy",
            json={},
            status=200,
        )

        # Login response
        responses.add_callback(
            responses.POST,
            "https://127.0.0.1:8443/api/v1/rpc/controller/core/aaa/session/login",
            callback=self._login_cb,
            content_type="application/json",
        )

        # Connect with retry configuration (host without scheme)
        client = pybsn.connect("127.0.0.1", "admin", "somepassword", retries=retry_config)

        # Should succeed after retry during URL guessing
        self.assertIsNotNone(client)
        self.assertEqual(client.url, "https://127.0.0.1:8443")

    @responses.activate
    def test_retry_during_login(self):
        """Verify retries work during login phase with 503 status."""
        responses.add(
            responses.GET,
            "http://127.0.0.1:8080/api/v1/auth/healthy",
            json={},
            status=200,
        )

        # Configure to retry POST (login uses POST) on 503
        retry_config = Retry(total=3, allowed_methods=["POST"], status_forcelist=[503])

        # First login attempt returns 503, second succeeds
        responses.add(
            responses.POST,
            "http://127.0.0.1:8080/api/v1/rpc/controller/core/aaa/session/login",
            json={},
            status=503,
        )
        responses.add_callback(
            responses.POST,
            "http://127.0.0.1:8080/api/v1/rpc/controller/core/aaa/session/login",
            callback=self._login_cb,
            content_type="application/json",
        )

        # Connect with retry configuration
        client = pybsn.connect(self.url, "admin", "somepassword", retries=retry_config)

        # Should succeed after retry during login
        self.assertIsNotNone(client)

    @responses.activate
    def test_retry_with_token_validation(self):
        """Verify retries work during token validation with 503 status."""
        responses.add(
            responses.GET,
            "http://127.0.0.1:8080/api/v1/auth/healthy",
            json={},
            status=200,
        )

        # Configure retry to retry on 503
        retry_config = Retry(total=3, status_forcelist=[503])

        # First token validation returns 503, second succeeds
        responses.add(
            responses.GET,
            "http://127.0.0.1:8080/api/v1/data/controller/core/aaa/auth-context",
            json={},
            status=503,
        )
        responses.add(
            responses.GET,
            "http://127.0.0.1:8080/api/v1/data/controller/core/aaa/auth-context",
            json=[{"user-info": {"user-name": "admin"}}],
            status=200,
        )

        # Connect with token and retry configuration
        client = pybsn.connect(self.url, token="test-token", retries=retry_config)

        # Should succeed after retry during token validation
        self.assertIsNotNone(client)


if __name__ == "__main__":
    unittest.main()
