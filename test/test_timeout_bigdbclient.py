import json
import requests
import responses
import sys
import unittest
from unittest.mock import patch
import urllib3

import pybsn

sys.path.append("test")
from fakeserver import FOREVER_BLOCKING_TIME
from mockutils import get_mockcall_attribute

MIDDLE_BLOCKING_TIME = FOREVER_BLOCKING_TIME / 2.0
SHORT_BLOCKING_TIME = MIDDLE_BLOCKING_TIME / 2.0
short_timeout = urllib3.util.Timeout(connect=SHORT_BLOCKING_TIME, read=SHORT_BLOCKING_TIME)
middle_timeout = urllib3.util.Timeout(connect=MIDDLE_BLOCKING_TIME, read=MIDDLE_BLOCKING_TIME)
long_timeout = urllib3.util.Timeout(connect=MIDDLE_BLOCKING_TIME * 2.0, read=MIDDLE_BLOCKING_TIME * 2.0)


class SuccessfulResponse:
    text = '{"schema":"big"}'

    def raise_for_status(self):
        pass



class TestTimeoutBigDbClient(unittest.TestCase):
    # noinspection GrazieInspection
    """Check that the timeout value passed to Session.send is correct.
           A timeout value is always passed through from BigDbClient calls.
        """
    url = "http://127.0.0.1:8080"

    def _assertTimeoutValue(self, expected_value, mock_call):
        actual = get_mockcall_attribute(mock_call, "timeout")
        self.assertEqual(expected_value, actual)
        return True

    def _login_cb(self, req):
        self.assertEqual(json.loads(req.body), {'user': 'admin', 'password': 'somepassword'})
        headers = {
            "Set-Cookie": "session_cookie=v_8yOI7FI-WKr-5QU6nxoJkVtAu5rKI-; Path=/api/;"
        }
        return (200, headers, json.dumps(
            {"success": True,
             "session-cookie": "UPhNWlmDN0re8cg9xsqe9QT1QvQTznji",
             "error-message": "",
             "past-login-info":
                 {"failed-login-count": 0,
                  "last-success-login-info": {"host": "127.0.0.1", "timestamp": "2019-05-19T19:16:22.328Z"}}}))

    def _add_login_responses(self):
        responses.add_callback(responses.HEAD,
                               "http://127.0.0.1:8080/api/v2/schema/controller/root/core/aaa/session/login",
                               callback=lambda req: (200, {}, ""),
                               content_type="application/json")
        responses.add_callback(responses.POST,
                               "http://127.0.0.1:8080/api/v1/rpc/controller/core/aaa/session/login",
                               callback=self._login_cb,
                               content_type="application/json")

    @responses.activate
    def test_get_timeout_default(self):
        """GET response retrieved with the default timeout which is None,
           meaning wait forever.
        """
        self._add_login_responses()

        client = pybsn.connect("http://127.0.0.1:8080", "admin", "somepassword")
        with patch.object(requests.Session, 'send') as mock_send:
            client.get(self.url)
            self._assertTimeoutValue(None, mock_send.mock_calls[0])

    @responses.activate
    def test_get_timeout_uses_client_default(self):
        """The timeout that is used when creating the client is used for
           GET when no override is specified.
        """
        self._add_login_responses()

        client = pybsn.connect("http://127.0.0.1:8080", "admin", "somepassword",
                               timeout=short_timeout)

        with patch.object(requests.Session, 'send') as mock_send:
            client.get(self.url)
            self._assertTimeoutValue(short_timeout, mock_send.mock_calls[0])

    @responses.activate
    def test_get_timeout_uses_client_default_float(self):
        """The timeout that is used when creating the client is used for
           GET when no override is specified.  Client default may be a float.
        """
        self._add_login_responses()

        client = pybsn.connect("http://127.0.0.1:8080", "admin", "somepassword",
                               timeout=SHORT_BLOCKING_TIME)

        with patch.object(requests.Session, 'send') as mock_send:
            client.get(self.url)
            self._assertTimeoutValue(SHORT_BLOCKING_TIME, mock_send.mock_calls[0])

    @responses.activate
    def test_get_timeout_arg(self):
        """GET specified timeout is used."""
        self._add_login_responses()
        client = pybsn.connect("http://127.0.0.1:8080", "admin", "somepassword")
        with patch.object(requests.Session, 'send') as mock_send:
            client.get(self.url, timeout=short_timeout)
            self._assertTimeoutValue(short_timeout, mock_send.mock_calls[0])

    @responses.activate
    def test_get_timeout_arg_none(self):
        """GET timeout argument of None indicates to wait forever."""
        self._add_login_responses()
        client = pybsn.connect("http://127.0.0.1:8080", "admin", "somepassword", timeout=short_timeout.read_timeout)
        with patch.object(requests.Session, 'send') as mock_send:
            client.get(self.url, timeout=None)
            self._assertTimeoutValue(None, mock_send.mock_calls[0])

    @responses.activate
    def test_get_timeout_arg_float(self):
        """GET timeout argument can be a float to indicate number
           of seconds."""
        timeout_arg = 42.1
        self._add_login_responses()
        client = pybsn.connect("http://127.0.0.1:8080", "admin", "somepassword", timeout=short_timeout.read_timeout)
        with patch.object(requests.Session, 'send') as mock_send:
            client.get(self.url, timeout=timeout_arg)
            self._assertTimeoutValue(timeout_arg, mock_send.mock_calls[0])

    @responses.activate
    def test_get_timeout_arg_client_timeout(self):
        """GET timeout argument of CLIENT_TIMEOUT indicates to use the timeout
          value from when BigDbClient was created.
        """
        self._add_login_responses()
        client = pybsn.connect(self.url, "admin", "somepassword",
                                                  timeout=middle_timeout.read_timeout)
        with patch.object(requests.Session, 'send') as mock_send:
            client.get(self.url, timeout=pybsn.CLIENT_TIMEOUT)
            self._assertTimeoutValue(middle_timeout.read_timeout, mock_send.mock_calls[0])

    @responses.activate
    def test_rpc_no_timeout(self):
        """RPC call without timeout usesNone which means waits forever until response."""
        self._add_login_responses()
        client = pybsn.connect(self.url, "admin", "somepassword")
        with patch.object(requests.Session, 'send') as mock_send:
            client.rpc(self.url, data={})
            self._assertTimeoutValue(None, mock_send.mock_calls[0])

    @responses.activate
    def test_rpc_timeout(self):
        """RPC call without timeout uses client default.
        """
        self._add_login_responses()
        client = pybsn.connect(self.url, "admin", "somepassword",
                                                  timeout=short_timeout)
        with patch.object(requests.Session, 'send') as mock_send:
            client.rpc(self.url, data={})
            self._assertTimeoutValue(short_timeout, mock_send.mock_calls[0])

    @responses.activate
    def test_rpc_timeout_arg(self):
        """RPC call uses timeout argument.
        """
        self._add_login_responses()
        client = pybsn.connect(self.url, "admin", "somepassword")
        with patch.object(requests.Session, 'send') as mock_send:
            client.rpc(self.url, data={}, timeout=short_timeout)
            self._assertTimeoutValue(short_timeout, mock_send.mock_calls[0])

    @responses.activate
    def test_post_no_timeout(self):
        """POST call without timeout uses default None."""
        self._add_login_responses()
        client = pybsn.connect(self.url, "admin", "somepassword")
        with patch.object(requests.Session, 'send') as mock_send:
            client.post(self.url, data={})
            self._assertTimeoutValue(None, mock_send.mock_calls[0])

    @responses.activate
    def test_post_timeout(self):
        """POST call without argument uses client default.
        """
        self._add_login_responses()
        client = pybsn.connect(self.url, "admin", "somepassword",
                                                  timeout=short_timeout)
        with patch.object(requests.Session, 'send') as mock_send:
            client.post(self.url, data={})
            self._assertTimeoutValue(short_timeout, mock_send.mock_calls[0])

    @responses.activate
    def test_post_timeout_arg(self):
        """POST call uses argument.
        """
        self._add_login_responses()
        client = pybsn.connect(self.url, "admin", "somepassword")
        with patch.object(requests.Session, 'send') as mock_send:
            client.post(self.url, data={}, timeout=short_timeout)
            self._assertTimeoutValue(short_timeout, mock_send.mock_calls[0])

    @responses.activate
    def test_put_no_timeout(self):
        """PUT call without timeout uses None."""
        self._add_login_responses()
        client = pybsn.connect(self.url, "admin", "somepassword")
        with patch.object(requests.Session, 'send') as mock_send:
            client.put(self.url, data={})
            self._assertTimeoutValue(None, mock_send.mock_calls[0])

    @responses.activate
    def test_put_timeout(self):
        """PUT call without argument uses client default.
        """
        self._add_login_responses()
        client = pybsn.connect(self.url, "admin", "somepassword",
                                                  timeout=short_timeout)
        with patch.object(requests.Session, 'send') as mock_send:
            client.put(self.url, data={})
            self._assertTimeoutValue(short_timeout, mock_send.mock_calls[0])

    @responses.activate
    def test_put_timeout_arg(self):
        """PUT call uses argument.
        """
        self._add_login_responses()
        client = pybsn.connect(self.url, "admin", "somepassword")
        with patch.object(requests.Session, 'send') as mock_send:
            client.put(self.url, data={}, timeout=short_timeout)
            self._assertTimeoutValue(short_timeout, mock_send.mock_calls[0])

    @responses.activate
    def test_patch_no_timeout(self):
        """PATCH call without timeout uses None."""
        self._add_login_responses()
        client = pybsn.connect(self.url, "admin", "somepassword")
        with patch.object(requests.Session, 'send') as mock_send:
            client.patch(self.url, data={})
            self._assertTimeoutValue(None, mock_send.mock_calls[0])

    @responses.activate
    def test_patch_timeout(self):
        """PATCH call without argument uses client default.
        """
        self._add_login_responses()
        client = pybsn.connect(self.url, "admin", "somepassword",
                                                  timeout=short_timeout)
        with patch.object(requests.Session, 'send') as mock_send:
            client.patch(self.url, data={})
            self._assertTimeoutValue(short_timeout, mock_send.mock_calls[0])

    @responses.activate
    def test_patch_timeout_arg(self):
        """PATCH call uses argument.
        """
        self._add_login_responses()
        client = pybsn.connect(self.url, "admin", "somepassword")
        with patch.object(requests.Session, 'send') as mock_send:
            client.patch(self.url, data={}, timeout=short_timeout)
            self._assertTimeoutValue(short_timeout, mock_send.mock_calls[0])

    @responses.activate
    def test_delete_no_timeout(self):
        """DELETE call without timeout uses None."""
        self._add_login_responses()
        client = pybsn.connect(self.url, "admin", "somepassword")
        with patch.object(requests.Session, 'send') as mock_send:
            client.delete(self.url)
            self._assertTimeoutValue(None, mock_send.mock_calls[0])

    @responses.activate
    def test_delete_timeout(self):
        """DELETE call without argument uses client default.
        """
        self._add_login_responses()
        client = pybsn.connect(self.url, "admin", "somepassword",
                                                  timeout=short_timeout)
        with patch.object(requests.Session, 'send') as mock_send:
            client.delete(self.url)
            self._assertTimeoutValue(short_timeout, mock_send.mock_calls[0])

    @responses.activate
    def test_delete_timeout_arg(self):
        """DELETE call uses argument.
        """
        self._add_login_responses()
        client = pybsn.connect(self.url, "admin", "somepassword")
        with patch.object(requests.Session, 'send') as mock_send:
            client.delete(self.url, timeout=short_timeout)
            self._assertTimeoutValue(short_timeout, mock_send.mock_calls[0])

    @responses.activate
    def test_schema_no_timeout(self):
        """SCHEMA call without timeout uses None."""
        self._add_login_responses()
        client = pybsn.connect(self.url, "admin", "somepassword")
        with patch.object(requests.Session, 'send') as mock_send:
            mock_send.return_value = SuccessfulResponse()
            client.schema(self.url)
            self._assertTimeoutValue(None, mock_send.mock_calls[0])

    @responses.activate
    def test_schema_timeout(self):
        """SCHEMA call will without argument uses client default.
        """
        self._add_login_responses()
        client = pybsn.connect(self.url, "admin", "somepassword",
                                                  timeout=short_timeout)
        with patch.object(requests.Session, 'send') as mock_send:
            mock_send.return_value = SuccessfulResponse()
            client.schema(self.url)
            self._assertTimeoutValue(short_timeout, mock_send.mock_calls[0])

    @responses.activate
    def test_schema_timeout_arg(self):
        """SCHEMA call uses argument.
        """
        self._add_login_responses()
        client = pybsn.connect(self.url, "admin", "somepassword")
        with patch.object(requests.Session, 'send') as mock_send:
            mock_send.return_value = SuccessfulResponse()
            client.schema(self.url, timeout=short_timeout)
            self._assertTimeoutValue(short_timeout, mock_send.mock_calls[0])

    @responses.activate
    def test_default_argument_can_be_changed(self):
        self._add_login_responses()
        client = pybsn.connect(self.url, "admin", "somepassword",
                                                  timeout=short_timeout)
        client.default_timeout = middle_timeout

        def has_new_timeout(mock_call):
            self._assertTimeoutValue(middle_timeout, mock_call)
            return True

        with patch.object(requests.Session, 'send') as mock_get:
            mock_get.return_value = SuccessfulResponse()
            client.schema(self.url)
            self.assertTrue(all(has_new_timeout(call) for call in mock_get.mock_calls))
            mock_get.assert_called()

    @responses.activate
    def test_default_argument_can_be_retrieved(self):
        self._add_login_responses()
        client = pybsn.connect(self.url, "admin", "somepassword",
                                                  timeout=short_timeout)
        self.assertEqual(short_timeout, client.default_timeout)
