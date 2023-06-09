#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""namespaces_json_server

Serves a fake Topology /osdf/namespaces JSON file on any GET.
Schema based on Topology 1.39.
Send a POST containing the word "bye" to shut down the server
"""
import sys
import json
import http.server
from http import HTTPStatus


HOST = "localhost"
PORT = 1080  # above 1024 and not used by any of our other services


def get_namespaces_json() -> str:
    """Get data for the /stashcache/namespaces JSON endpoint.

    This includes a list of caches, with some data about cache endpoints,
    and a list of namespaces with some data about each namespace; see README.md for details.
    """
    # These values taken from test_150_stashcache.py
    osg_test_cache = {
        "endpoint": "localhost:8001",
        "auth_endpoint": "localhost:8444",
        "resource": "OSG_TEST_CACHE"
    }

    namespaces = [
        {
            "path": "/osgtest/PUBLIC",
            "readhttps": False,
            "usetokenonread": False,
            "writebackhost": None,
            "dirlisthost": None,
            "caches": [osg_test_cache],
            "credential_generation": None,
        },
        {
            "path": "/osgtest/PROTECTED",
            "readhttps": True,
            "usetokenonread": True,
            "writebackhost": None,
            "dirlisthost": None,
            "caches": [osg_test_cache],
            "credential_generation": None,
        }
    ]

    return json.dumps({
        "caches": [ osg_test_cache ],
        "namespaces": namespaces
    }, sort_keys=True)


class HTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    def __init__(self, request, client_address, server):
        super().__init__(request, client_address, server)

    def do_GET(self):
        """GET handler

        Respond with the namespaces json
        """
        self.send_response(HTTPStatus.OK)
        # I copied these headers from what Topology sends back from /osdf/namespaces/json
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "max-age=300, stale-while-revalidate=100")
        self.send_header("Vary", "Accept-Encoding")
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        response = get_namespaces_json().encode()
        self.log_request(code=HTTPStatus.OK, size=len(response))
        self.wfile.write(response)

    def do_POST(self):
        """POST handler

        if given a POST with "bye" in it, shuts down the server
        """
        # a little overkill -- I could have shut down the server on any POST
        # but it took long enough to figure out the Content-Length thing that
        # I wanted to keep the code.
        content_length = int(self.headers.get("Content-Length", 0))
        # need to check the content length before reading, otherwise empty
        # POST data would make us block.
        data = b""
        if content_length:
            data = self.rfile.read1()
        if b"bye" in data:
            code = HTTPStatus.NO_CONTENT
            self.log_request(code, size=0)
            self.log_message("exiting")
            self.send_response(code)
            self.end_headers()
            sys.exit(0)
        else:
            code = HTTPStatus.BAD_REQUEST
            self.log_request(code, size=0)
            self.log_error("bad POST")
            self.send_response(code)
            self.end_headers()


def main(argv):
    server_address = (HOST, PORT)
    httpd = http.server.HTTPServer(server_address, HTTPRequestHandler)
    print(f"Server created on {HOST}:{PORT}.\n"
          "Serving namespaces JSON on any GET.\n"
          "Send a POST containing 'bye' to exit")
    httpd.serve_forever()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
