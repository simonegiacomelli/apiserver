import base64
import json
from http.server import SimpleHTTPRequestHandler
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse, parse_qs


class RequestHandler(SimpleHTTPRequestHandler):
    auth_file = Path('.auth.txt')  # username:password see RFC 7617
    query_index = 4
    path_index = 2

    def __init__(self, *args
                 , handler: Callable[['RequestHandler'], bool]
                 , **kwargs):
        self.handler = handler
        super(RequestHandler, self).__init__(*args, **kwargs)

    def do_GET(self):
        if not self.authorized():
            self.send_string('not authorized', code=401)
            return
        if not self.handler(self):
            super(RequestHandler, self).do_GET()

    def decode_request(self):
        p = urlparse(self.path)
        query_str = p[self.query_index]
        rpath = p[self.path_index]
        di = parse_qs(query_str)
        params = {k: v[0] for k, v in di.items()}
        return params, rpath

    def authorized(self):
        if not self.auth_file.exists():
            return True
        auth_raw = self.headers.get('Authorization', '').split(' ')
        if len(auth_raw) != 2 or auth_raw[0] != 'Basic':
            return False
        auth_decoded = base64.b64decode(auth_raw[1]).decode('utf-8')
        return auth_decoded == self.auth_file.read_text()

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
        self.send_header("WWW-Authenticate", "Basic")
        self.end_headers()
        self.wfile.write(bytes(message, "utf8"))

    def serve_file(self, directory, filename):
        self.directory = directory
        self.path = '/' + filename
        super(RequestHandler, self).do_GET()
