import http.server
import http.server
import json
import os
import sys
import threading
import time
import unittest
from http.server import HTTPServer
from itertools import cycle, repeat
import requests
from requests import exceptions as request_exception
import pybsn
import urllib3
from unittest.mock import patch
sys.path.append("test")
from fakeserver import FOREVER_BLOCKING_TIME, FakeServer
from mockutils import get_mockcall_attribute

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

    def test_connect_default_timeout(self):
        with patch.object(requests.Session, 'send') as mock_send:
            client = pybsn.connect("http://127.0.0.1:8080", "admin", "somepassword")
            self._assertTimeoutValue(None, mock_send.mock_calls[0])
            self.assertIsNone(client.default_timeout)

    def test_connect_timeout(self):
        timeout = urllib3.util.Timeout(10, 10)
        with patch.object(requests.Session, 'send') as mock_send:
            client = pybsn.connect("http://127.0.0.1:8080",
                                   "admin", "somepassword",
                                   timeout=timeout)
            self._assertTimeoutValue(timeout, mock_send.mock_calls[0])
            self.assertEqual(timeout, client.default_timeout)

    def test_connect_token_default_timeout(self):
        with patch.object(requests.Session, 'send') as mock_send:
            client = pybsn.connect("http://127.0.0.1:8080", "admin",
                                   token="sometoken")
            self._assertTimeoutValue(None, mock_send.mock_calls[0])
            self.assertIsNone(client.default_timeout)

    def test_connect_token_timeout(self):
        with patch.object(requests.Session, 'send') as mock_send:
            timeout = urllib3.util.Timeout(10, 10)
            client = pybsn.connect("http://127.0.0.1:8080", "admin",
                                   token="sometoken",
                                   timeout=timeout)
            self._assertTimeoutValue(timeout, mock_send.mock_calls[0])
            self.assertEqual(timeout, client.default_timeout)

    def test_connect_timeout_legacy_login(self):
        timeout = urllib3.util.Timeout(10, 10)

        def has_timeout(mock_call):
            self._assertTimeoutValue(timeout, mock_call)
            return True

        with patch.object(requests.Session, 'send') as mock_send:
            first_response = requests.Response()
            first_response.status_code = 201
            second_response = requests.Response()
            second_response.status_code = 200
            mock_send.side_effect =iter( [first_response, second_response])
            client = pybsn.connect("http://127.0.0.1:8080",
                                   "admin", "somepassword",
                                   timeout=timeout)

            mock_send.assert_called()
            self.assertTrue(all(has_timeout(call) for call in  mock_send.mock_calls))

    def test_connect_timeout_modern_login(self):
        timeout = urllib3.util.Timeout(10, 10)

        def has_timeout(mock_call):
            self._assertTimeoutValue(timeout, mock_call)
            return True

        with patch.object(requests.Session, 'send') as mock_send:
            first_response = requests.Response()
            first_response.status_code = 200
            second_response = requests.Response()
            second_response.status_code = 200
            second_response.json = lambda : {'session-cookie':'chocolate-chip'}
            mock_send.side_effect =iter( [first_response, second_response])
            client = pybsn.connect("http://127.0.0.1:8080",
                                   "admin", "somepassword",
                                   timeout=timeout)
            mock_send.assert_called()
            self.assertTrue(all(has_timeout(call) for call in  mock_send.mock_calls))
