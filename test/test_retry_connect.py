import sys
import unittest
from unittest.mock import MagicMock, patch

import requests
from urllib3.util.retry import Retry

import pybsn

sys.path.append("test")


class TestRetryConnect(unittest.TestCase):
    """
    Test that the retry parameter is properly configured during connection setup.
    """

    def test_connect_no_retries(self):
        """Default behavior (retries=None), verify no custom HTTPAdapter mounted."""
        with patch.object(requests.Session, "send") as mock_send:
            mock_send.return_value = self._create_mock_response(200, {"session-cookie": "test-cookie"})
            client = pybsn.connect("http://127.0.0.1:8080", "admin", "password")
            # Verify session has default adapters (not custom retry adapters)
            # Default sessions have basic HTTPAdapters with max_retries=0 (Retry(0))
            adapter = client.session.get_adapter("http://example.com")
            self.assertIsInstance(adapter, requests.adapters.HTTPAdapter)
            # Default adapter has max_retries=0 or Retry(0, read=False)
            if isinstance(adapter.max_retries, int):
                self.assertEqual(adapter.max_retries, 0)
            else:
                # Default Retry object has total=0
                self.assertEqual(adapter.max_retries.total, 0)

    def test_connect_retries_int(self):
        """Pass retries=3, verify HTTPAdapter mounted with correct int value."""
        with patch.object(requests.Session, "send") as mock_send:
            mock_send.return_value = self._create_mock_response(200, {"session-cookie": "test-cookie"})
            client = pybsn.connect("http://127.0.0.1:8080", "admin", "password", retries=3)

            # Verify adapters have max_retries configured with total=3
            # Note: int gets converted to Retry object by urllib3
            http_adapter = client.session.get_adapter("http://example.com")
            https_adapter = client.session.get_adapter("https://example.com")

            self.assertIsInstance(http_adapter, requests.adapters.HTTPAdapter)
            self.assertIsInstance(https_adapter, requests.adapters.HTTPAdapter)
            self.assertIsInstance(http_adapter.max_retries, Retry)
            self.assertIsInstance(https_adapter.max_retries, Retry)
            self.assertEqual(http_adapter.max_retries.total, 3)
            self.assertEqual(https_adapter.max_retries.total, 3)

    def test_connect_retries_retry_object(self):
        """Pass Retry(total=5, backoff_factor=0.5), verify correct object."""
        retry_config = Retry(total=5, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])

        with patch.object(requests.Session, "send") as mock_send:
            mock_send.return_value = self._create_mock_response(200, {"session-cookie": "test-cookie"})
            client = pybsn.connect("http://127.0.0.1:8080", "admin", "password", retries=retry_config)

            # Verify adapters have the correct Retry object
            http_adapter = client.session.get_adapter("http://example.com")
            https_adapter = client.session.get_adapter("https://example.com")

            self.assertIsInstance(http_adapter, requests.adapters.HTTPAdapter)
            self.assertIsInstance(https_adapter, requests.adapters.HTTPAdapter)
            self.assertEqual(http_adapter.max_retries, retry_config)
            self.assertEqual(https_adapter.max_retries, retry_config)

    def test_connect_retries_with_token(self):
        """Retries work with token auth."""
        with patch.object(requests.Session, "send") as mock_send:
            mock_send.return_value = self._create_mock_response(200, [])
            client = pybsn.connect("http://127.0.0.1:8080", token="test-token", retries=3)

            # Verify adapters have max_retries configured with total=3
            # Note: int gets converted to Retry object by urllib3
            http_adapter = client.session.get_adapter("http://example.com")
            https_adapter = client.session.get_adapter("https://example.com")

            self.assertIsInstance(http_adapter, requests.adapters.HTTPAdapter)
            self.assertIsInstance(https_adapter, requests.adapters.HTTPAdapter)
            self.assertIsInstance(http_adapter.max_retries, Retry)
            self.assertIsInstance(https_adapter.max_retries, Retry)
            self.assertEqual(http_adapter.max_retries.total, 3)
            self.assertEqual(https_adapter.max_retries.total, 3)

    def test_connect_retries_preserves_verify_tls_true(self):
        """Verify TLS verification still works when verify_tls=True and retries set."""
        with patch.object(requests.Session, "mount"):
            with patch.object(requests.Session, "send") as mock_send:
                mock_send.return_value = self._create_mock_response(200, {"session-cookie": "test-cookie"})
                client = pybsn.connect("http://127.0.0.1:8080", "admin", "password", verify_tls=True, retries=3)

                # Verify TLS verification is enabled
                self.assertTrue(client.session.verify)

    def test_connect_retries_preserves_verify_tls_false(self):
        """Verify TLS verification disabled when verify_tls=False and retries set."""
        with patch.object(requests.Session, "mount"):
            with patch.object(requests.Session, "send") as mock_send:
                mock_send.return_value = self._create_mock_response(200, {"session-cookie": "test-cookie"})
                client = pybsn.connect("http://127.0.0.1:8080", "admin", "password", verify_tls=False, retries=3)

                # Verify TLS verification is disabled
                self.assertFalse(client.session.verify)

    def _create_mock_response(self, status_code, json_data):
        """Helper to create a mock response object."""
        response = MagicMock(spec=requests.Response)
        response.status_code = status_code
        response.json.return_value = json_data
        response.raise_for_status.return_value = None
        return response


if __name__ == "__main__":
    unittest.main()
