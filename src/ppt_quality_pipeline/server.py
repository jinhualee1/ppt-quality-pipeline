from __future__ import annotations

import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from .io import read_json, write_json


def _web_root() -> Path:
    return Path(__file__).resolve().parent / "web"


class ReviewServer(ThreadingHTTPServer):
    def __init__(self, address: tuple[str, int], run_dir: Path):
        self.run_dir = run_dir.resolve()
        self.web_root = _web_root()
        super().__init__(address, ReviewHandler)


class ReviewHandler(BaseHTTPRequestHandler):
    server: ReviewServer

    def log_message(self, format: str, *args: object) -> None:
        print(f"[review] {self.address_string()} {format % args}")

    def _send_json(self, value: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        payload = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def _send_file(self, path: Path) -> None:
        if not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        payload = path.read_bytes()
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _safe_run_path(self, raw_path: str) -> Path | None:
        candidate = (self.server.run_dir / unquote(raw_path)).resolve()
        try:
            candidate.relative_to(self.server.run_dir)
        except ValueError:
            return None
        return candidate

    def do_GET(self) -> None:
        route = urlparse(self.path).path
        if route == "/api/report":
            self._send_json(read_json(self.server.run_dir / "report.json"))
            return
        if route == "/api/annotations":
            annotations = self.server.run_dir / "annotations.json"
            self._send_json(read_json(annotations) if annotations.is_file() else {})
            return
        if route.startswith("/assets/"):
            candidate = self._safe_run_path(route.removeprefix("/assets/"))
            if candidate is None:
                self.send_error(HTTPStatus.FORBIDDEN)
            else:
                self._send_file(candidate)
            return
        asset = "index.html" if route in {"", "/"} else route.lstrip("/")
        candidate = (self.server.web_root / asset).resolve()
        try:
            candidate.relative_to(self.server.web_root)
        except ValueError:
            self.send_error(HTTPStatus.FORBIDDEN)
            return
        self._send_file(candidate)

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/annotations":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(payload, dict):
                raise TypeError("Annotations must be an object.")
            write_json(self.server.run_dir / "annotations.json", payload)
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            self._send_json({"ok": False, "error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        self._send_json({"ok": True, "count": len(payload)})


def serve(run_dir: Path, host: str = "127.0.0.1", port: int = 8765) -> None:
    run_dir = run_dir.resolve()
    if not (run_dir / "report.json").is_file():
        raise FileNotFoundError(f"Run report does not exist: {run_dir / 'report.json'}")
    server = ReviewServer((host, port), run_dir)
    print(f"Review workspace: http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
