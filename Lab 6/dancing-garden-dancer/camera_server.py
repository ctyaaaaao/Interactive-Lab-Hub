
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.request import urlopen
from urllib.error import URLError

CAMERA = "http://127.0.0.1:8080/snapshot"

class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.split("?")[0] == "/snapshot":
            try:
                with urlopen(CAMERA, timeout=5) as response:
                    data = response.read()

                self.send_response(200)
                self.send_header("Content-Type", "image/jpeg")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            except (URLError, TimeoutError) as error:
                self.send_error(502, str(error))
        else:
            super().do_GET()

server = ThreadingHTTPServer(
    ("127.0.0.1", 8000), Handler
)
print("Dancing Garden: http://localhost:8000", flush=True)
server.serve_forever()
