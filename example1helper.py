#!/usr/bin/env python3

import getpass
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Example1RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_string(f'Pid={os.getpid()}\n'
                         f'user={getpass.getuser()}\n'
                         f'hostname={os.uname().nodename}\n'
                         f'clock={time.time()}')

    def send_string(self, message, code=200):
        self.protocol_version = "HTTP/1.1"
        self.send_response(code)
        self.send_header("Content-Length", str(len(message)))
        self.end_headers()
        self.wfile.write(bytes(message, "utf8"))


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('port', action='store',
                        default=5000, type=int,
                        nargs='?',
                        help='Specify alternate port [default: 5000]')
    args = parser.parse_args()

    with ThreadingHTTPServer(("", args.port), Example1RequestHandler) as httpd:
        host, port = httpd.socket.getsockname()[:2]
        url_host = f'[{host}]' if ':' in host else host
        print(
            f"Serving HTTP on {host} port {port} "
            f"(http://{url_host}:{port}/) ..."
        )
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nKeyboard interrupt received, exiting.")
            sys.exit(0)
