"""A private loopback preview of exactly one generated ontology HTML file.

The detached server survives MCP restarts, serves no workspace directory, and
exits after an idle timeout. Codex opens its URL in its own browser panel.
"""
from __future__ import annotations

import argparse
import json
import os
import secrets
import subprocess
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.error import URLError
from urllib.request import ProxyHandler, build_opener

_OPENER = build_opener(ProxyHandler({}))
STATE_FILE = "preview-server.json"


def _healthy(state: dict, html_path: Path) -> bool:
    if state.get("html_path") != str(html_path):
        return False
    port = state.get("port")
    token = state.get("token")
    if not isinstance(port, int) or not 1 <= port <= 65535 or not isinstance(token, str):
        return False
    try:
        with _OPENER.open(f"http://127.0.0.1:{port}/{token}/health", timeout=0.5) as response:
            return json.load(response).get("token") == token
    except (OSError, URLError, ValueError):
        return False


def ensure_preview(html_path: Path) -> str:
    html_path = html_path.resolve()
    if not html_path.is_file():
        raise FileNotFoundError(html_path)
    state_path = html_path.parent / STATE_FILE
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        state = {}
    if _healthy(state, html_path):
        return state["url"]
    token = secrets.token_urlsafe(24)
    command = [sys.executable, str(Path(__file__).resolve()), "--html", str(html_path),
               "--token", token]
    options = {"stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL,
               "stderr": subprocess.DEVNULL, "close_fds": True}
    if os.name == "nt":
        options["creationflags"] = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        options["start_new_session"] = True
    process = subprocess.Popen(command, **options)
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("Ontology preview server exited before becoming ready")
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            state = {}
        if state.get("token") == token and _healthy(state, html_path):
            return state["url"]
        time.sleep(0.05)
    process.terminate()
    raise RuntimeError("Ontology preview server did not become ready")


def serve(html_path: Path, token: str, idle_seconds: float = 3600) -> None:
    html_path = html_path.resolve()
    last_request = time.monotonic()
    base_path = "/" + token + "/"

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            nonlocal last_request
            if self.headers.get("Host") != f"127.0.0.1:{self.server.server_port}":
                self.send_error(403)
                return
            path = self.path.split("?", 1)[0]
            if path == base_path + "health":
                content = json.dumps({"token": token}).encode()
                content_type = "application/json"
            elif path == base_path + "ontology.html":
                try:
                    content = html_path.read_bytes()
                except OSError:
                    self.send_error(404)
                    return
                content_type = "text/html; charset=utf-8"
            else:
                self.send_error(404)
                return
            last_request = time.monotonic()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            try:
                self.wfile.write(content)
            except (BrokenPipeError, ConnectionResetError):
                pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    server.timeout = 0.5
    state = {"pid": os.getpid(), "port": server.server_port, "token": token,
             "html_path": str(html_path),
             "url": f"http://127.0.0.1:{server.server_port}{base_path}ontology.html"}
    state_path = html_path.parent / STATE_FILE
    temporary = state_path.with_suffix("." + token + ".tmp")
    temporary.write_text(json.dumps(state), encoding="utf-8")
    temporary.replace(state_path)
    try:
        while time.monotonic() - last_request < idle_seconds:
            server.handle_request()
    finally:
        server.server_close()
        try:
            if json.loads(state_path.read_text(encoding="utf-8")).get("token") == token:
                state_path.unlink()
        except (OSError, ValueError):
            pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--html", required=True)
    parser.add_argument("--token", required=True)
    args = parser.parse_args()
    serve(Path(args.html), args.token)
