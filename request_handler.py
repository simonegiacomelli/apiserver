import json
from http.server import SimpleHTTPRequestHandler
from typing import Callable
from urllib.parse import urlparse, parse_qs


class RequestHandler(SimpleHTTPRequestHandler):
    query_index = 4
    path_index = 2

    def __init__(self, *args
                 , handler: Callable[['RequestHandler'], bool]
                 , **kwargs):
        self.handler = handler
        super(RequestHandler, self).__init__(*args, **kwargs)

    def do_GET(self):
        if not self.handler(self):
            super(RequestHandler, self).do_GET()

    def decode_request(self):
        p = urlparse(self.path)
        query_str = p[self.query_index]
        rpath = p[self.path_index]
        di = parse_qs(query_str)
        params = {k: v[0] for k, v in di.items()}
        return params, rpath

    def send_json(self, obj):
        self.send_string(json.dumps(obj, indent=2), content_type='application/json')

    def send_string(self, message, code=200, content_type='text/plain'):
        self.protocol_version = "HTTP/1.1"
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(message)))
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "*")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(bytes(message, "utf8"))

    def serve_file(self, directory, filename):
        self.directory = directory
        self.path = '/' + filename
        super(RequestHandler, self).do_GET()
