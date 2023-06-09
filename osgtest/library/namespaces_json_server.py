#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""namespaces_json_server

Serves a fake Topology /osdf/namespaces JSON file on any GET.
Schema based on Topology 1.39.
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


def main(argv):
    server_address = (HOST, PORT)
    httpd = http.server.HTTPServer(server_address, HTTPRequestHandler)
    print(f"Server created on {HOST}:{PORT}.\n"
          "Serving namespaces JSON on any GET.\n"
          "Send SIGTERM to exit")
    httpd.serve_forever()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
