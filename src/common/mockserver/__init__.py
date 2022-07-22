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
from typing import Dict, List, Optional, Union, Iterator, Tuple
from urllib.parse import parse_qs, urlsplit

logger = logging.getLogger(__file__)
common_dir = str(pathlib.Path(__file__).absolute().parent.parent)


class RequestHandler(http.server.SimpleHTTPRequestHandler):

    def __init__(self, *args, directory=None, callback=None, response_provider=None, **kwargs):
        self.callback = callback or (lambda request: None)
        self.response_provider = response_provider or (lambda path, query_params: None)
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
        self.callback(Request(self.path, self.query_params, self.timestamp))
        response = self.response_provider(self.path, self.query_params)
        response: Union[None, str, Tuple[int, Iterator[Tuple[str, str]], Union[None, str, bytes]]]
        if response is None:
            return super().do_GET()
        elif isinstance(response, str):
            response = HTTPStatus.OK, [], response
        code, headers, body = response
        self.send_response(code)
        content_type_sent = False
        for key, value in headers:
            self.send_header(key, value)
            if key.lower() == 'content-type':
                content_type_sent = True
        if body is None:
            self.end_headers()
        else:
            if isinstance(body, str):
                body = body.encode()
            if not content_type_sent:
                self.send_header("Content-Type", self.guess_type(self.path))
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    def do_POST(self):
        body = self.rfile.read(int(self.headers['Content-Length']))
        self.callback(Request(self.path, self.query_params, self.timestamp, body))


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


class MockServer:
    def __init__(self, port=0, directory='.', response_provider=None):
        self.server_name = 'https://fledge-tests.creativecdn.net'
        self.server_port = port
        self.server_directory = directory
        self.requests = []

        logger.debug(f"server {self.address} initializing")
        server_address = ('0.0.0.0', self.server_port)
        self.http_server = http.server.ThreadingHTTPServer(
            server_address,
            partial(RequestHandler, directory=self.server_directory, response_provider=response_provider,
                    callback=self.requests.append))
        self.server_port = self.http_server.server_port
        self.http_server.socket = ssl.wrap_socket(
            self.http_server.socket,
            server_side=True,
            certfile=common_dir + '/ssl/fledge-tests.creativecdn.net.crt',
            keyfile=common_dir + '/ssl/fledge-tests.creativecdn.net.key',
            ssl_version=ssl.PROTOCOL_TLS)

    @property
    def address(self):
        return f'{self.server_name}:{self.server_port}'

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
