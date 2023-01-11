# Copyright 2021 RTBHOUSE. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
import http.server
import json
import logging
import pathlib
import ssl
import threading
import time
from dataclasses import dataclass
from functools import partial
from http import HTTPStatus
from typing import Dict, List, Optional, Union, Iterable, Tuple, Callable
from urllib.parse import parse_qs, urlsplit

logger = logging.getLogger(__file__)
common_dir = str(pathlib.Path(__file__).absolute().parent.parent)


@dataclass(init=True, repr=True, eq=False, frozen=True)
class Request:
    path: str
    params: Dict[str, List[str]]
    timestamp: float
    body: Optional[bytes] = None

    def get_params(self, key):
        return self.params[key]

    def get_first_param(self, key):
        return self.get_params(key)[0]

    def get_first_json_param(self, key):
        return json.loads(self.get_first_param(key))


@dataclass
class Response:
    status: HTTPStatus
    headers: Iterable[Tuple[str, str]]
    body: Union[None, str, bytes]


class RequestHandler(http.server.SimpleHTTPRequestHandler):
    callback: Callable[[Request], Optional[Response]]

    def __init__(self, *args, directory=None, callback=None, **kwargs):
        self.callback = callback or (lambda request: None)
        super().__init__(*args, directory=directory, **kwargs)

    def end_headers(self) -> None:
        self.send_header('X-Allow-FLEDGE', 'true')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Supports-Loading-Mode', 'fenced-frame')
        return super().end_headers()

    def address_string(self):
        return f'{self.client_address[0]} -> :{self.server.server_port}'

    def parse_request(self) -> bool:
        if not super().parse_request():
            return False
        self.path, query = urlsplit(self.path)[2:4]
        self.query_params = parse_qs(query)
        self.timestamp = time.time()
        logger.info(
            f"{self.command} request path: {self.path}, query params: {self.query_params}")
        return True

    def do_GET(self):
        response = self.callback(Request(self.path, self.query_params, self.timestamp))
        if response is None:
            return super().do_GET()
        self.send_response(response.status)
        content_type_sent = False
        for key, value in response.headers:
            self.send_header(key, value)
            if key.lower() == 'content-type':
                content_type_sent = True
        if response.body is None:
            self.end_headers()
        else:
            body: bytes
            if isinstance(response.body, str):
                body = response.body.encode()
            else:
                body = response.body
            if not content_type_sent:
                self.send_header("Content-Type", self.guess_type(self.path))
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    def do_POST(self):
        body = self.rfile.read(int(self.headers['Content-Length']))
        response = self.callback(Request(self.path, self.query_params, self.timestamp, body))
        if not response:
            self.send_response(HTTPStatus.OK)
            self.end_headers()


class MockServer:
    def __init__(self, port=0, directory='.', name='localhost',
                 response_provider: Callable[[Request], Optional[Response]] = None):
        self.server_directory = directory
        self.requests = []

        def callback(request: Request):
            self.requests.append(request)
            if response_provider:
                return response_provider(request)

        self.http_server = http.server.ThreadingHTTPServer(
            (name, port),
            partial(RequestHandler, directory=self.server_directory, callback=callback))
        self.server_name = name or self.http_server.server_name
        self.server_port = port or self.http_server.server_port
        self.http_server.socket = ssl.wrap_socket(
            self.http_server.socket,
            server_side=True,
            certfile=common_dir + '/ssl/localhost.crt',
            keyfile=common_dir + '/ssl/localhost.key',
            ssl_version=ssl.PROTOCOL_TLS)
        logger.info(f"server {self.address} initialized")

    @property
    def address(self):
        return f'https://{self.server_name}:{self.server_port}'

    def __enter__(self):
        logger.debug(f"server {self.address} starting")
        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()
        return self

    def run(self):
        self.http_server.serve_forever()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.http_server.socket.close()
        self.http_server.shutdown()
        logger.debug(f"server {self.address} stopped")

    def get_requests(self):
        return self.requests

    def get_last_request(self, path) -> Optional[Request]:
        result = None
        for request in self.get_requests():
            if request.path == path:
                result = request
        return result
