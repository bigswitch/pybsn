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
from requests.exceptions import ReadTimeout
from urllib3.exceptions import ReadTimeoutError
from unittest.mock import patch

import pybsn

sys.path.append("test")
from fakeserver import FakeServer, FOREVER_BLOCKING_TIME

MIDDLE_BLOCKING_TIME = FOREVER_BLOCKING_TIME / 2.0
short_timeout = pybsn.TimeoutSauce(connect=MIDDLE_BLOCKING_TIME / 2.0, read=MIDDLE_BLOCKING_TIME / 2.0)
long_timeout = pybsn.TimeoutSauce(connect=MIDDLE_BLOCKING_TIME * 2.0, read=MIDDLE_BLOCKING_TIME * 2.0)


class SuccessfulResponse:
    text = '{"schema":"big"}'

    def raise_for_status(self):
        pass


class TestTimeoutBigDbClientIntegration(unittest.TestCase):
    """Check that actual calls using BigDbClient will timeout.

       We are just checking that Session.send responds to the timeout parameter
       as expected.  None indicates to wait forever, otherwise the TimeoutSauce
       is used.

       The pybsn code will always pass a timeout parameter.
    """
    server: FakeServer = None

    def setUp(self) -> None:
        self.server = FakeServer()
        self.server.server._testMethodName = self._testMethodName
        self.url = f"http://127.0.0.1:{self.server.port()}"

    def tearDown(self) -> None:
        self.server.stop()

    def test_timeout_sauce_arg_causes_timeout(self):
        """Verify that request.Session.Send will time out when
           passed a TimeoutSauce.
        """
        self.server.start()
        client: pybsn.BigDbClient = pybsn.connect(self.url, "admin", "a_password")
        with self.assertRaises(ReadTimeout):
            self.server.get_blocking(repeat(long_timeout.read_timeout, times=1))
            client.get(self.url, timeout=short_timeout)

    def test_none_waits_for_response(self):
        """Verify that request.Session.Send will wait for a response when
           timeout is none.
        """
        self.server.start()
        client: pybsn.BigDbClient = pybsn.connect(self.url, "admin", "a_password")
        self.server.get_blocking(repeat(long_timeout.read_timeout, times=1))
        client.get(self.url)

    def test_quick_response(self):
        """Verify that request.Session.Send will wait process the response
           if it arrives prior to the timeout.
        """
        self.server.start()
        client: pybsn.BigDbClient = pybsn.connect(self.url, "admin", "a_password")
        self.server.get_blocking(repeat(short_timeout.read_timeout, times=1))
        client.get(self.url, timeout=long_timeout)

    def test_quick_response(self):
        """Verify that request.Session.Send will wait process the response
           if it arrives prior to the timeout.
        """
        self.server.start()
        client: pybsn.BigDbClient = pybsn.connect(self.url, "admin", "a_password")
        self.server.get_blocking(repeat(short_timeout.read_timeout, times=1))
        client.get(self.url, timeout=long_timeout)
