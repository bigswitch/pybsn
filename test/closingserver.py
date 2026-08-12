import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, List, Optional, Tuple, Union

QueuedAction = Tuple[Union[str, int], Optional[bytes], Optional[Dict[str, str]]]
RequestRecord = Dict[str, Any]


class ClosingServer(HTTPServer):
    thread: Optional[threading.Thread]

    def __init__(self, server_address: Tuple[str, int] = ("127.0.0.1", 0)) -> None:
        super().__init__(server_address, ClosingHandler)
        self._actions: List[QueuedAction] = []
        self._requests: List[RequestRecord] = []
        self._lock = threading.Lock()
        self.thread = None

    def queue_drop_next_request(self) -> None:
        with self._lock:
            self._actions.append(("drop_next_request", None, None))

    def queue_close_with_last_response(self) -> None:
        with self._lock:
            self._actions.append(("close_with_last_response", None, None))

    def queue_json(self, payload: Any, status: int = 200) -> None:
        body = json.dumps(payload).encode("utf8")
        response_headers = {"Content-Type": "application/json"}
        self.queue_response(status=status, body=body, headers=response_headers)

    def queue_response(self, status: int = 200, body: bytes = b"", headers: Optional[Dict[str, str]] = None) -> None:
        with self._lock:
            self._actions.append((status, body, headers or {}))

    def next_action(self) -> QueuedAction:
        with self._lock:
            if not self._actions:
                raise Exception("No queued action for test server")
            return self._actions.pop(0)

    def consume_close_with_last_response(self) -> bool:
        with self._lock:
            if self._actions and self._actions[0][0] == "close_with_last_response":
                self._actions.pop(0)
                return True
            return False

    def record_request(self, method: str, path: str, connection_id: Any) -> None:
        with self._lock:
            self._requests.append({"connection_id": connection_id, "method": method, "path": path})

    def requests(self) -> List[RequestRecord]:
        with self._lock:
            return list(self._requests)

    def request_count(self) -> int:
        with self._lock:
            return len(self._requests)

    def start(self) -> bool:
        try:
            self.thread = threading.Thread(name="ClosingServer", target=self.serve_forever)
            self.thread.start()
            return True
        except Exception:
            print(f"unable to start server on port {self.server_port}")
            return False

    def port(self) -> int:
        return self.server_port

    def stop(self) -> None:
        if self.thread and self.thread.is_alive():
            self.shutdown()
        if self.thread:
            self.thread.join(timeout=60)
            if self.thread.is_alive():
                raise Exception("Server thread did not terminate")
        self.server_close()


class ClosingHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length", "0"))
        if length:
            return self.rfile.read(length)
        return b""

    def _handle(self) -> None:
        self._read_body()
        self.server.record_request(self.command, self.path, self.client_address)

        action = self.server.next_action()
        if action[0] == "drop_next_request":
            self.close_connection = True
            self.connection.shutdown(socket.SHUT_RDWR)
            self.connection.close()
            return

        status, response_body, headers = action
        assert isinstance(status, int)
        assert response_body is not None
        assert headers is not None
        should_close_with_last_response = self.server.consume_close_with_last_response()
        self.send_response(status)
        if should_close_with_last_response:
            self.send_header("Connection", "close")
        for key, value in headers.items():
            self.send_header(key, value)
        if "Content-Length" not in headers:
            self.send_header("Content-Length", str(len(response_body)))
        self.end_headers()
        if response_body:
            self.wfile.write(response_body)
            self.wfile.flush()
        if should_close_with_last_response:
            self.close_connection = True
            try:
                self.connection.shutdown(socket.SHUT_RDWR)
            except OSError:
                # The client may have already closed its side after reading the response.
                pass
            self.connection.close()

    def do_DELETE(self) -> None:
        self._handle()

    def do_GET(self) -> None:
        self._handle()

    def do_POST(self) -> None:
        self._handle()

    def do_PATCH(self) -> None:
        self._handle()

    def do_PUT(self) -> None:
        self._handle()

    def log_message(self, format: str, *args: Any) -> None:
        return
