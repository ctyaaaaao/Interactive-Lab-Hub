
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import urlopen
from urllib.error import URLError

class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.split("?")[0] == "/camera.jpg":
            try:
                with urlopen(
                    "http://127.0.0.1:8080/snapshot",
                    timeout=3
                ) as response:
                    image = response.read()

                self.send_response(200)
                self.send_header("Content-Type", "image/jpeg")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(image)))
                self.end_headers()
                self.wfile.write(image)

            except (URLError, TimeoutError, OSError) as e:
                self.send_error(502, str(e))
            return

        super().do_GET()

if __name__ == "__main__":
    server = ThreadingHTTPServer(
        ("127.0.0.1", 8000), Handler
    )
    print("Dancing Garden: http://localhost:8000")
    server.serve_forever()
