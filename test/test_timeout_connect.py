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
import pybsn
from unittest.mock import patch
sys.path.append("test")
from fakeserver import FOREVER_BLOCKING_TIME, FakeServer
from requests import exceptions as request_exception

class TestTimeoutConnect(unittest.TestCase):
    """
    Test that connecting to the server can timeout, and that the
    parameter passed when connecting is used as the default value
    for future REST operations on the session.
    """

    def test_connect_default_timeout(self):
        with patch.object(requests.Session, 'send') as mock_send:
            client = pybsn.connect("http://127.0.0.1:8080", "admin", "somepassword")
            self.assertIsNone(mock_send.mock_calls[0].kwargs['timeout'])
            self.assertIsNone(client.get_default_timeout())

    def test_connect_timeout(self):
        timeout = pybsn.TimeoutSauce(10, 10)
        with patch.object(requests.Session, 'send') as mock_send:
            client = pybsn.connect("http://127.0.0.1:8080",
                                   "admin", "somepassword",
                                   timeout=timeout)
            self.assertEqual(timeout, mock_send.mock_calls[0].kwargs['timeout'])
            self.assertEqual(timeout, client.get_default_timeout())

    def test_connect_token_default_timeout(self):
        with patch.object(requests.Session, 'send') as mock_send:
            client = pybsn.connect("http://127.0.0.1:8080", "admin",
                                   token="sometoken")
            self.assertIsNone(mock_send.mock_calls[0].kwargs['timeout'])
            self.assertIsNone(client.get_default_timeout())

    def test_connect_token_timeout(self):
        with patch.object(requests.Session, 'send') as mock_send:
            timeout = pybsn.TimeoutSauce(10, 10)
            client = pybsn.connect("http://127.0.0.1:8080", "admin",
                                   token="sometoken",
                                   timeout=timeout)
            self.assertEqual(timeout, mock_send.mock_calls[0].kwargs['timeout'])
            self.assertEqual(timeout, client.get_default_timeout())
