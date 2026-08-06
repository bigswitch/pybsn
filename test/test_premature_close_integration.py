import unittest
from test.closingserver import ClosingServer

import requests

import pybsn


class TestPrematureCloseIntegration(unittest.TestCase):
    def setUp(self):
        self.server = ClosingServer()
        self.assertTrue(self.server.start())
        self.url = f"http://127.0.0.1:{self.server.port()}"

    def tearDown(self):
        self.server.stop()

    def _call_method(self, client, method):
        fn = getattr(client, method.lower())
        if method in ("GET", "DELETE"):
            return fn("controller/test")
        return fn("controller/test", data={"foo": "bar"})

    def _assert_idempotent_method_retries_after_keep_alive_premature_close(self, method):
        self.server.queue_json({"state": "warmup"})
        self.server.queue_drop_next_request()
        self.server.queue_json({"state": "ok"})
        self.server.queue_close_with_last_response()

        client = pybsn.connect(self.url)

        self.assertEqual({"state": "warmup"}, client.get("controller/test"))
        result = self._call_method(client, method)
        if method == "GET":
            self.assertEqual({"state": "ok"}, result)
        else:
            self.assertEqual(200, result.status_code)

        requests_log = self.server.requests()
        self.assertEqual(3, self.server.request_count(), msg=f"unexpected request log: {requests_log}")
        self.assertEqual(
            [
                ("GET", "/api/v1/data/controller/test"),
                (method, "/api/v1/data/controller/test"),
                (method, "/api/v1/data/controller/test"),
            ],
            [(request["method"], request["path"]) for request in requests_log],
            msg=f"unexpected request log: {requests_log}",
        )
        self.assertEqual(
            requests_log[0]["connection_id"],
            requests_log[1]["connection_id"],
            msg=f"expected keep-alive reuse before retry: {requests_log}",
        )
        self.assertNotEqual(
            requests_log[1]["connection_id"],
            requests_log[2]["connection_id"],
            msg=f"expected retry on a new TCP connection: {requests_log}",
        )

    def test_get_retries_after_keep_alive_premature_close(self):
        self._assert_idempotent_method_retries_after_keep_alive_premature_close("GET")

    def test_put_retries_after_keep_alive_premature_close(self):
        self._assert_idempotent_method_retries_after_keep_alive_premature_close("PUT")

    def test_delete_retries_after_keep_alive_premature_close(self):
        self._assert_idempotent_method_retries_after_keep_alive_premature_close("DELETE")

    def test_post_does_not_retry_after_keep_alive_premature_close(self):
        self.server.queue_json({"state": "warmup"})
        self.server.queue_drop_next_request()

        client = pybsn.connect(self.url)

        self.assertEqual({"state": "warmup"}, client.get("controller/test"))
        with self.assertRaises(requests.exceptions.ConnectionError):
            client.post("controller/test", data={"foo": "bar"})

        requests_log = self.server.requests()
        self.assertEqual(2, self.server.request_count(), msg=f"unexpected request log: {requests_log}")
        self.assertEqual(
            [
                ("GET", "/api/v1/data/controller/test"),
                ("POST", "/api/v1/data/controller/test"),
            ],
            [(request["method"], request["path"]) for request in requests_log],
            msg=f"unexpected request log: {requests_log}",
        )
        self.assertEqual(
            requests_log[0]["connection_id"],
            requests_log[1]["connection_id"],
            msg=f"expected stale keep-alive POST to arrive on the reused socket: {requests_log}",
        )

    def test_patch_does_not_retry_after_keep_alive_premature_close(self):
        self.server.queue_json({"state": "warmup"})
        self.server.queue_drop_next_request()

        client = pybsn.connect(self.url)

        self.assertEqual({"state": "warmup"}, client.get("controller/test"))
        with self.assertRaises(requests.exceptions.ConnectionError):
            client.patch("controller/test", data={"foo": "bar"})

        requests_log = self.server.requests()
        self.assertEqual(2, self.server.request_count(), msg=f"unexpected request log: {requests_log}")
        self.assertEqual(
            [
                ("GET", "/api/v1/data/controller/test"),
                ("PATCH", "/api/v1/data/controller/test"),
            ],
            [(request["method"], request["path"]) for request in requests_log],
            msg=f"unexpected request log: {requests_log}",
        )
        self.assertEqual(
            requests_log[0]["connection_id"],
            requests_log[1]["connection_id"],
            msg=f"expected stale keep-alive PATCH to arrive on the reused socket: {requests_log}",
        )
