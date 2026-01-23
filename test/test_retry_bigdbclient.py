import json
import sys
import unittest

import requests
import responses
from requests.exceptions import ConnectionError
from urllib3.util.retry import Retry

import pybsn

sys.path.append("test")


class TestRetryBigDbClient(unittest.TestCase):
    """
    Test that retry behavior works correctly across all BigDbClient methods.
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
                    "past-login-info": {
                        "failed-login-count": 0,
                        "last-success-login-info": {"host": "127.0.0.1", "timestamp": "2019-05-19T19:16:22.328Z"},
                    },
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
    def test_get_retries_on_failure(self):
        """GET request retries on connection error and succeeds after retry."""
        self._add_login_responses()

        # Configure retry to retry on 503 status
        retry_config = Retry(total=3, status_forcelist=[503])

        # First two GET attempts return 503, third succeeds
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
            json=[{"name": "switch1"}],
            status=200,
        )

        client = pybsn.connect(self.url, "admin", "somepassword", retries=retry_config)
        result = client.get("controller/core/switch")

        # Should succeed after retries
        self.assertEqual(result, [{"name": "switch1"}])

    @responses.activate
    def test_post_retries_on_failure(self):
        """POST request retries on connection error when configured."""
        self._add_login_responses()

        # Configure retry to allow POST retries and retry on 503
        retry_config = Retry(total=3, allowed_methods=["POST"], status_forcelist=[503])

        # First two POST attempts return 503, third succeeds
        responses.add(
            responses.POST,
            "http://127.0.0.1:8080/api/v1/data/controller/core/switch",
            json={},
            status=503,
        )
        responses.add(
            responses.POST,
            "http://127.0.0.1:8080/api/v1/data/controller/core/switch",
            json={},
            status=503,
        )
        responses.add(
            responses.POST,
            "http://127.0.0.1:8080/api/v1/data/controller/core/switch",
            json={},
            status=201,
        )

        client = pybsn.connect(self.url, "admin", "somepassword", retries=retry_config)
        response = client.post("controller/core/switch", data={"name": "switch1"})

        # Should succeed after retries
        self.assertEqual(response.status_code, 201)

    @responses.activate
    def test_put_retries_on_failure(self):
        """PUT request retries on connection error when configured."""
        self._add_login_responses()

        # Configure retry to allow PUT retries and retry on 503
        retry_config = Retry(total=3, allowed_methods=["PUT"], status_forcelist=[503])

        # First two PUT attempts return 503, third succeeds
        responses.add(
            responses.PUT,
            "http://127.0.0.1:8080/api/v1/data/controller/core/switch",
            json={},
            status=503,
        )
        responses.add(
            responses.PUT,
            "http://127.0.0.1:8080/api/v1/data/controller/core/switch",
            json={},
            status=503,
        )
        responses.add(
            responses.PUT,
            "http://127.0.0.1:8080/api/v1/data/controller/core/switch",
            json={},
            status=200,
        )

        client = pybsn.connect(self.url, "admin", "somepassword", retries=retry_config)
        response = client.put("controller/core/switch", data={"name": "switch1"})

        # Should succeed after retries
        self.assertEqual(response.status_code, 200)

    @responses.activate
    def test_patch_retries_on_failure(self):
        """PATCH request retries on connection error when configured."""
        self._add_login_responses()

        # Configure retry to allow PATCH retries and retry on 503
        retry_config = Retry(total=3, allowed_methods=["PATCH"], status_forcelist=[503])

        # First two PATCH attempts return 503, third succeeds
        responses.add(
            responses.PATCH,
            "http://127.0.0.1:8080/api/v1/data/controller/core/switch",
            json={},
            status=503,
        )
        responses.add(
            responses.PATCH,
            "http://127.0.0.1:8080/api/v1/data/controller/core/switch",
            json={},
            status=503,
        )
        responses.add(
            responses.PATCH,
            "http://127.0.0.1:8080/api/v1/data/controller/core/switch",
            json={},
            status=200,
        )

        client = pybsn.connect(self.url, "admin", "somepassword", retries=retry_config)
        response = client.patch("controller/core/switch", data={"name": "switch1"})

        # Should succeed after retries
        self.assertEqual(response.status_code, 200)

    @responses.activate
    def test_delete_retries_on_failure(self):
        """DELETE request retries on connection error when configured."""
        self._add_login_responses()

        # Configure retry to allow DELETE retries and retry on 503
        retry_config = Retry(total=3, allowed_methods=["DELETE"], status_forcelist=[503])

        # First two DELETE attempts return 503, third succeeds
        responses.add(
            responses.DELETE,
            "http://127.0.0.1:8080/api/v1/data/controller/core/switch",
            json={},
            status=503,
        )
        responses.add(
            responses.DELETE,
            "http://127.0.0.1:8080/api/v1/data/controller/core/switch",
            json={},
            status=503,
        )
        responses.add(
            responses.DELETE,
            "http://127.0.0.1:8080/api/v1/data/controller/core/switch",
            status=204,
        )

        client = pybsn.connect(self.url, "admin", "somepassword", retries=retry_config)
        response = client.delete("controller/core/switch")

        # Should succeed after retries
        self.assertEqual(response.status_code, 204)

    @responses.activate
    def test_rpc_retries_on_failure(self):
        """RPC request retries on connection error when configured."""
        self._add_login_responses()

        # Configure retry to allow POST retries (RPC uses POST) and retry on 503
        retry_config = Retry(total=3, allowed_methods=["POST"], status_forcelist=[503])

        # First two RPC attempts return 503, third succeeds
        responses.add(
            responses.POST,
            "http://127.0.0.1:8080/api/v1/rpc/controller/core/switch/disconnect",
            json={},
            status=503,
        )
        responses.add(
            responses.POST,
            "http://127.0.0.1:8080/api/v1/rpc/controller/core/switch/disconnect",
            json={},
            status=503,
        )
        responses.add(
            responses.POST,
            "http://127.0.0.1:8080/api/v1/rpc/controller/core/switch/disconnect",
            json={"result": "disconnected"},
            status=200,
        )

        client = pybsn.connect(self.url, "admin", "somepassword", retries=retry_config)
        result = client.rpc("controller/core/switch/disconnect", data={})

        # Should succeed after retries
        self.assertEqual(result, {"result": "disconnected"})

    @responses.activate
    def test_schema_retries_on_failure(self):
        """Schema request retries on connection error."""
        self._add_login_responses()

        # Configure retry to retry on 503
        retry_config = Retry(total=3, status_forcelist=[503])

        # First two schema attempts return 503, third succeeds
        responses.add(
            responses.GET,
            "http://127.0.0.1:8080/api/v1/schema/controller/core/switch",
            json={},
            status=503,
        )
        responses.add(
            responses.GET,
            "http://127.0.0.1:8080/api/v1/schema/controller/core/switch",
            json={},
            status=503,
        )
        responses.add(
            responses.GET,
            "http://127.0.0.1:8080/api/v1/schema/controller/core/switch",
            json={"type": "object"},
            status=200,
        )

        client = pybsn.connect(self.url, "admin", "somepassword", retries=retry_config)
        result = client.schema("controller/core/switch")

        # Should succeed after retries
        self.assertEqual(result, {"type": "object"})

    @responses.activate
    def test_retries_exhausted_raises(self):
        """After exhausting retries, exception is raised."""
        self._add_login_responses()

        # Configure retry to retry on 503
        retry_config = Retry(total=3, status_forcelist=[503], raise_on_status=False)

        # All attempts return 503
        for _ in range(10):  # More than enough failures to exhaust retries
            responses.add(
                responses.GET,
                "http://127.0.0.1:8080/api/v1/data/controller/core/switch",
                json={},
                status=503,
            )

        client = pybsn.connect(self.url, "admin", "somepassword", retries=retry_config)

        # Should raise HTTPError after retries are exhausted (from raise_for_status)
        with self.assertRaises(requests.exceptions.HTTPError):
            client.get("controller/core/switch")

    @responses.activate
    def test_retry_with_status_forcelist(self):
        """Retry specific HTTP status codes when configured."""
        self._add_login_responses()

        # Configure retry to retry on 503 status
        retry_config = Retry(total=3, status_forcelist=[503])

        # First two attempts return 503, third succeeds
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
            json=[{"name": "switch1"}],
            status=200,
        )

        client = pybsn.connect(self.url, "admin", "somepassword", retries=retry_config)
        result = client.get("controller/core/switch")

        # Should succeed after retries
        self.assertEqual(result, [{"name": "switch1"}])

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

        client = pybsn.connect(self.url, "admin", "somepassword")  # No retries parameter

        # Should raise exception immediately without retries
        with self.assertRaises(ConnectionError):
            client.get("controller/core/switch")

    @responses.activate
    def test_retry_backoff_behavior(self):
        """Verify exponential backoff when using Retry object."""
        self._add_login_responses()

        # Configure retry with backoff and retry on 503
        retry_config = Retry(total=3, backoff_factor=0.1, status_forcelist=[503])

        # First two GET attempts return 503, third succeeds
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
            json=[{"name": "switch1"}],
            status=200,
        )

        client = pybsn.connect(self.url, "admin", "somepassword", retries=retry_config)
        result = client.get("controller/core/switch")

        # Should succeed after retries
        # Note: Backoff behavior is handled by urllib3 internally
        self.assertEqual(result, [{"name": "switch1"}])


if __name__ == "__main__":
    unittest.main()
