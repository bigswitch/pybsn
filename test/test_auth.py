import json
import unittest
from unittest.mock import patch

import requests

import pybsn


class TestAuth(unittest.TestCase):
    def test_attempt_login_posts_credentials_and_stores_session_cookie(self):
        session = requests.Session()
        response = requests.Response()
        response.status_code = 200
        response.json = lambda: {"session-cookie": "some_token"}

        with patch.object(pybsn, "logged_request", return_value=response) as mock_logged_request:
            pybsn._attempt_login(session, "http://127.0.0.1:8080", "admin", "somepassword")

        _, request = mock_logged_request.call_args.args
        self.assertEqual(request.method, "POST")
        self.assertEqual(request.url, "http://127.0.0.1:8080/api/v1/rpc/controller/core/aaa/session/login")
        self.assertEqual(json.loads(request.data), {"user": "admin", "password": "somepassword"})
        self.assertEqual(session.cookies.get_dict(), {"session_cookie": "some_token"})

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
