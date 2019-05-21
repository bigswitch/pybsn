import json
import os
import logging
import unittest

import requests

import pybsn
import responses

my_dir = os.path.dirname(__file__)

class TestBigDbClient(unittest.TestCase):
    def setUp(self):
        self.client = pybsn.connect("http://127.0.0.1:8080")

    @responses.activate
    def test_connect_login(self):
        def _login_cb(req):
            self.assertEqual(json.loads(req.body), {'user': 'admin', 'password': 'somepassword'})
            headers = {
                "Set-Cookie": "session_cookie=v_8yOI7FI-WKr-5QU6nxoJkVtAu5rKI-; Path=/api/;"
            }
            return (200, headers, json.dumps(
                {"success": True,
                 "session_cookie": "UPhNWlmDN0re8cg9xsqe9QT1QvQTznji",
                 "error_message": "",
                 "past_login_info":
                     {"failed_login_count": 0,
                      "last_success_login_info": {"host": "127.0.0.1", "timestamp": "2019-05-19T19:16:22.328Z"}}}))

        responses.add_callback(responses.POST, "http://127.0.0.1:8080/api/v1/auth/login", callback=_login_cb,
                               content_type="application/json")

        client = pybsn.connect("http://127.0.0.1:8080", "admin", "somepassword")

        # Responses is currently broken in that it doesn't retain the session cookies...
        # https://github.com/getsentry/responses/issues/80
        #
        # self.assertEqual(client.session.cookies, {"Cookie": "session_cookie=UPhNWlmDN0re8cg9xsqe9QT1QvQTznji"})
        #
        # def _get_cb(req):
        #     self.assertEqual(req.headers["Cookie"], "session_cookie=UPhNWlmDN0re8cg9xsqe9QT1QvQTznji")
        #     return (200, {}, json.dumps([ "ok" ]))
        #
        # responses.add_callback(responses.GET, "http://127.0.0.1:8080/api/v1/data/controller/test", callback=_get_cb,
        #                        content_type="application/json")
        # client.get("controller/test")

    @responses.activate
    def test_connect_wrong_pw(self):
        def _login_cb(req):
            self.assertEqual(json.loads(req.body), {'user': 'admin', 'password': 'foo'})
            headers = {
                "Set-Cookie": "session_cookie=v_8yOI7FI-WKr-5QU6nxoJkVtAu5rKI-; Path=/api/;"
            }
            return (401, headers, json.dumps(
                {"success":False,
                 "session_cookie":None,
                 "error_message":"Invalid user/password combination.",
                 "past_login_info":None}))

        responses.add_callback(responses.POST, "http://127.0.0.1:8080/api/v1/auth/login", callback=_login_cb,
                               content_type="application/json")

        with self.assertRaises(requests.exceptions.HTTPError) as context:
            pybsn.connect("http://127.0.0.1:8080", "admin", "foo")
        self.assertEqual(context.exception.response.status_code, 401)

    @responses.activate
    def test_connect_token(self):
        def _aaa_cb(req):
            self.assertEqual(req.headers["Cookie"], "session_cookie=some_token")
            return (200, {}, json.dumps([ {  "auth-context-type" : "session-token",  "user-info" :
                              {   "full-name" : "Default admin",
                             "group" : [ "admin" ],    "user-name" : "admin"  } } ])
                    )

        responses.add_callback(responses.GET, "http://127.0.0.1:8080/api/v1/data/controller/core/aaa/auth-context",
                               callback=_aaa_cb, content_type="application/json")

        pybsn.connect("http://127.0.0.1:8080", token="some_token")

    @responses.activate
    def test_connect_token_wrong(self):
        def _aaa_cb(req):
            self.assertEqual(req.headers["Cookie"], "session_cookie=wrong_token")
            return (401, {}, json.dumps({
                "description":"Authorization failed: No session or token found for cookie",
                "error-code":401
            }))

        responses.add_callback(responses.GET, "http://127.0.0.1:8080/api/v1/data/controller/core/aaa/auth-context",
                               callback=_aaa_cb, content_type="application/json")

        with self.assertRaises(requests.exceptions.HTTPError) as context:
            pybsn.connect("http://127.0.0.1:8080", token="wrong_token")
        self.assertEqual(context.exception.response.status_code, 401)

    @responses.activate
    def test_rpc(self):
        responses.add(responses.POST, "http://127.0.0.1:8080/api/v1/rpc/controller/rpc",
                      json={'id': 1234}, status=200)
        result = self.client.rpc(path="controller/rpc",
                                 data={"description": "desc"})
        self.assertEqual(result, {'id': 1234})

    @responses.activate
    def test_no_response(self):
        responses.add(responses.POST, "http://127.0.0.1:8080/api/v1/rpc/controller/rpc",
                      status=204)
        result = self.client.rpc(path="controller/rpc",
                                 data={"description": "desc"})
        self.assertIsNone(result)
