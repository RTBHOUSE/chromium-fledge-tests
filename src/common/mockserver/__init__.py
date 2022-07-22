# Copyright 2021 RTBHOUSE. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.
import http.server
import json
import logging
import pathlib
import ssl
import threading
from dataclasses import dataclass
from functools import partial
from typing import Dict, List, Optional
from urllib.parse import parse_qs, urlsplit

logger = logging.getLogger(__file__)
common_dir = str(pathlib.Path(__file__).absolute().parent.parent)


class RequestHandler(http.server.SimpleHTTPRequestHandler):

    def __init__(self, *args, directory, callback, **kwargs):
        self.callback = callback
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
        logger.info(
            f"{self.command} request path: {self.path}, query params: {self.query_params}")
        return True

    def do_GET(self):
        self.callback(Request(self.path, self.query_params))

        if self.path.startswith("/report") or self.path.startswith("/debug") or self.path.startswith('/favicon'):
            pass
        else:
            super().do_GET()

    def do_POST(self):
        body = self.rfile.read(int(self.headers['Content-Length']))
        self.callback(Request(self.path, self.query_params, body))


@dataclass(init=True, repr=True, eq=False, frozen=True)
class Request:
    path: str
    params: Dict[str, List[str]]
    body: Optional[bytes] = None

    def get_params(self, key):
        return self.params[key]

    def get_first_param(self, key):
        return self.get_params(key)[0]

    def get_first_json_param(self, key):
        return json.loads(self.get_first_param(key))


class MockServer:
    def __init__(self, port, directory):
        self.server_name = 'https://fledge-tests.creativecdn.net'
        self.server_port = port
        self.server_directory = directory
        self.http_server = None
        self.requests = []

        logger.debug(f"server {self.address} initializing")
        server_address = ('0.0.0.0', self.server_port)
        self.http_server = http.server.ThreadingHTTPServer(
            server_address,
            partial(RequestHandler, directory=self.directory, callback=self.requests.append))
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

    @property
    def directory(self):
        return self.server_directory

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
