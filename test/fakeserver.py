import json
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from itertools import repeat
from typing import Iterable

# How long to wait in seconds before sending a response in a test
# case where we are checking that we will wait forever.
FOREVER_BLOCKING_TIME = 10


class BlockingServer(HTTPServer):

    # Amount of time to wait, in seconds, before sending a GET response.
    get_blocking = repeat(StopIteration, 1)

    # Has the server been _stopped so it no longer needs to
    # return responses.
    _stopped = False
    _lock = threading.Lock()

    # noinspection PyPep8Naming
    def __init__(self, server_address, RequestHandlerClass):
        super().__init__(server_address, RequestHandlerClass)

    def is_stopped(self) :
        """
        :returns: boolean
        """
        with self._lock:
            return self._stopped

    def shutdown(self):
        super().shutdown()
        with self._lock:
            self._stopped = True


class FakeHandler(BaseHTTPRequestHandler):
    """Override the server type from BaseServer."""

    def _server(self) :
        """Casting self.server for Python checking.
        :return: BlockingServer
        """
        # noinspection PyTypeChecker
        return self.server

    def _block(self, delay_list) :
        """Delay for a period of time.

        Attributes:
            delay_list: Iterable. Top value will be removed and used as the minimum number
            of seconds to wait.  The actual delay may be longer.
        """
        delay = delay_list.__next__()
        if delay == StopIteration:
            # noinspection PyProtectedMember
            msg = f"delay_list is empty: {self._server()._testMethodName}"
            raise Exception(msg)

        end_time = time.monotonic() + delay
        while time.monotonic() < end_time and not self._server().is_stopped():
            time.sleep(0.5)

    # noinspection PyPep8Naming
    def do_HEAD(self):
        if self._server().is_stopped():
            self.send_error(500, "server is _stopped")
            return
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.close_connection = True

    # noinspection PyPep8Naming
    def do_GET(self):
        self._block(self._server().get_blocking)
        if self._server().is_stopped():
            self.send_error(500, "server is _stopped")
            return
        result = [{"auth-context-type": "session-token",
                   "user-info": {"full-name": "Default admin",
                                 "group": ["admin"], "user-name": "admin"}}]
        result_as_str = json.dumps(result)
        result_as_bytes = bytes(result_as_str, "utf8")
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_header("content-length", str(len(result_as_bytes)))
        self.end_headers()
        self.wfile.write(result_as_bytes)
        self.close_connection = True

    # noinspection PyPep8Naming
    def do_OPTIONS(self):
        if self._server().is_stopped():
            self.send_error(500, "server is _stopped")
            return
        result = ["OPTIONS"]
        result_as_str = json.dumps(result)
        result_as_bytes = bytes(result_as_str, "utf8")
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_header("content-length", str(len(result_as_bytes)))
        self.end_headers()
        self.wfile.write(result_as_bytes)
        self.close_connection = True

    # noinspection PyPep8Naming
    def do_POST(self):
        if self._server().is_stopped():
            self.send_error(500, "server is _stopped")
            return
        result_as_str = json.dumps(
            {"success": True,
             "session-cookie": "UPhNWlmDN0re8cg9xsqe9QT1QvQTznji",
             "error-message": "",
             "past-login-info":
                 {"failed-login-count": 0,
                  "last-success-login-info": {"host": "127.0.0.1", "timestamp": "2019-05-19T19:16:22.328Z"}}})
        result_as_bytes = bytes(result_as_str, "utf8")
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_header("content-length", str(len(result_as_bytes)))
        self.end_headers()
        self.wfile.write(result_as_bytes)
        self.close_connection = True

    # noinspection PyPep8Naming
    def do_PUT(self):
        if self._server().is_stopped():
            self.send_error(500, "server is _stopped")
            return
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_header("content-length", "0")
        self.end_headers()
        self.close_connection = True

    # noinspection PyPep8Naming
    def do_PATCH(self):
        if self._server().is_stopped():
            self.send_error(500, "server is _stopped")
            return
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_header("content-length", "0")
        self.end_headers()
        self.close_connection = True

    # noinspection PyPep8Naming
    def do_DELETE(self):
        if self._server().is_stopped():
            self.send_error(500, "server is _stopped")
            return
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_header("content-length", "0")
        self.end_headers()
        self.close_connection = True


class FakeServer:
    thread = None
    server = None

    def __init__(self):
        super().__init__()
        self.server = BlockingServer(('localhost', 0), FakeHandler)

    def _run_server(self):
        self.server.serve_forever()

    def get_blocking(self, delay):
        """Set the amount of time to wait prior to responding to
           a GET request.

           :parameter delay Amount of seconds to wait. Iterable[float]
        """
        self.server.get_blocking = delay


    def start(self):
        # noinspection PyBroadException
        try:
            self.thread = threading.Thread(
                name="FakeServer",
                target=self._run_server)
            self.thread.start()
            return True
        except Exception:
            print(f'unable to start server on port {self.server.server_port}')
            return False

    def port(self):
        """:return port the server is listening on."""
        return self.server.server_port

    def stop(self):
        if self.thread.is_alive():
            self.server.shutdown()
        self.thread.join(timeout=60)
        if self.thread.is_alive():
            raise Exception("Server thread did not terminate")
