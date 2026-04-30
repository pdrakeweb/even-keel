"""HTTP reverse proxy for the Claude preview tool.

The preview tool's browser runs in a sandbox that can't reach host
localhost directly. This script binds to whatever port the preview tool
provides (PORT env var) and reverse-proxies all requests to
http://localhost:8123 (Home Assistant in Docker).

Pure stdlib — no Flask / aiohttp / etc. Suitable for screenshot and
basic navigation; not for WebSocket-heavy live HA use, but plenty for
preview screenshots of static pages and forms.
"""
import os
import sys
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TARGET = os.environ.get("PROXY_TARGET", "http://localhost:8123")
PORT = int(os.environ.get("PORT", "8124"))
HOP_BY_HOP = {
    "connection", "keep-alive", "proxy-authenticate",
    "proxy-authorization", "te", "trailers", "transfer-encoding", "upgrade",
}


class ProxyHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _proxy(self, method: str) -> None:
        url = TARGET + self.path
        body_len = int(self.headers.get("Content-Length", "0") or 0)
        body = self.rfile.read(body_len) if body_len else None
        headers = {
            k: v for k, v in self.headers.items()
            if k.lower() not in HOP_BY_HOP and k.lower() != "host"
        }
        req = urllib.request.Request(url=url, data=body, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                self.send_response(resp.status)
                for k, v in resp.headers.items():
                    if k.lower() in HOP_BY_HOP or k.lower() == "content-length":
                        continue
                    self.send_header(k, v)
                content = resp.read()
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            content = e.read() or b""
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:  # noqa: BLE001
            sys.stderr.write(f"[proxy] error: {e}\n")
            self.send_response(502)
            msg = f"Bad Gateway: {e}".encode()
            self.send_header("Content-Length", str(len(msg)))
            self.end_headers()
            self.wfile.write(msg)

    def do_GET(self): self._proxy("GET")
    def do_POST(self): self._proxy("POST")
    def do_PUT(self): self._proxy("PUT")
    def do_DELETE(self): self._proxy("DELETE")
    def do_HEAD(self): self._proxy("HEAD")
    def do_PATCH(self): self._proxy("PATCH")

    def log_message(self, format, *args):
        sys.stderr.write("[proxy] " + format % args + "\n")


def main() -> None:
    server = ThreadingHTTPServer(("0.0.0.0", PORT), ProxyHandler)
    print(f"Preview proxy listening on :{PORT} -> {TARGET}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()


if __name__ == "__main__":
    main()
