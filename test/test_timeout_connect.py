import sys
import unittest
from unittest.mock import patch

import requests
import urllib3

import pybsn

sys.path.append("test")
from mockutils import get_mockcall_attribute  # noqa: E402


class TestTimeoutConnect(unittest.TestCase):
    """
    Test that connecting to the server can timeout, and that the
    parameter passed when connecting is used as the default value
    for future REST operations on the session.
    """

    def _assertTimeoutValue(self, expected_value, mock_call):
        actual = get_mockcall_attribute(mock_call, "timeout")
        self.assertEqual(expected_value, actual)
        return True

    def _assertAllCallsTimeoutValue(self, expected_value, mock_function):
        """Verify that the mock function was called, and that all calls
        have a timeout argument set to the expected value.
        """
        mock_function.assert_called()

        def compare_value(call):
            if call[0].startswith("()."):
                # Not a REST call ignore.
                # We could filter instead.
                return True
            return self._assertTimeoutValue(expected_value, call)

        self.assertTrue(all(compare_value(call) for call in mock_function.mock_calls))

    def test_connect_default_timeout(self):
        with patch.object(requests.Session, "send") as mock_send:
            client = pybsn.connect("http://127.0.0.1:8080", "admin", "somepassword")
            self._assertAllCallsTimeoutValue(None, mock_send)
            self.assertIsNone(client.default_timeout)

    def test_connect_timeout(self):
        timeout = urllib3.util.Timeout(10, 10)
        with patch.object(requests.Session, "send") as mock_send:
            client = pybsn.connect("http://127.0.0.1:8080", "admin", "somepassword", timeout=timeout)
            self._assertAllCallsTimeoutValue(timeout, mock_send)
            self.assertEqual(timeout, client.default_timeout)

    def test_connect_token_default_timeout(self):
        with patch.object(requests.Session, "send") as mock_send:
            client = pybsn.connect("http://127.0.0.1:8080", "admin", token="sometoken")
            self._assertAllCallsTimeoutValue(None, mock_send)
            self.assertIsNone(client.default_timeout)

    def test_connect_token_timeout(self):
        timeout = urllib3.util.Timeout(10, 10)
        with patch.object(requests.Session, "send") as mock_send:
            client = pybsn.connect("http://127.0.0.1:8080", "admin", token="sometoken", timeout=timeout)
            self._assertAllCallsTimeoutValue(timeout, mock_send)
            self.assertEqual(timeout, client.default_timeout)

    def test_connect_timeout_modern_login(self):
        timeout = urllib3.util.Timeout(10, 10)
        with patch.object(requests.Session, "send") as mock_send:
            first_response = requests.Response()
            first_response.status_code = 200
            first_response.json = lambda: {"session-cookie": "chocolate-chip"}
            mock_send.side_effect = iter([first_response])
            pybsn.connect("http://127.0.0.1:8080", "admin", "somepassword", timeout=timeout)
            self._assertAllCallsTimeoutValue(timeout, mock_send)

    def test_attempt_login_cookie_matches_ipv4_and_ipv6_urls(self):
        for url in ("http://127.0.0.1:8080", "https://[fdfd::1]:8443"):
            with self.subTest(url=url):
                session = requests.Session()
                response = requests.Response()
                response.status_code = 200
                response.json = lambda: {"session-cookie": "some_token"}

                with patch.object(pybsn, "logged_request", return_value=response):
                    pybsn._attempt_login(session, url, "admin", "somepassword")

                request = requests.Request("GET", url + "/api/v1/data/controller/test")
                prepared_request = session.prepare_request(request)
                self.assertEqual(prepared_request.headers["Cookie"], "session_cookie=some_token")
