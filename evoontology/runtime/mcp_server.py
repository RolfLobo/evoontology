"""Dependency-free stdio MCP server for the active EvoOntology workspace."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

if __package__:
    from ..workspace import resolve_workspace, resolve_workspace_for_version
    from . import ops
    from .runtime import SemanticLayer
    from .tools import OPERATIONS, TOOLS
else:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from evoontology.runtime import ops
    from evoontology.runtime.runtime import SemanticLayer
    from evoontology.runtime.tools import OPERATIONS, TOOLS
    from evoontology.workspace import resolve_workspace, resolve_workspace_for_version

_RESOURCE_URI = "evo-semantic://session-manifest"

PARSE_ERROR = -32700
METHOD_NOT_FOUND = -32601
INTERNAL_ERROR = -32603


def force_utf8_stdio() -> None:
    """Serve UTF-8 regardless of the host locale.

    MCP stdio traffic is always UTF-8, but a plugin server inherits the host
    process environment. On Windows that means the console code page (for
    example GBK) is used for stdin/stdout unless told otherwise. Incoming
    UTF-8 bytes then decode to mojibake that can corrupt JSON escapes, and
    outgoing non-ASCII text can fail to encode -- either way the client waits
    for a reply that never arrives. Reconfiguring the streams makes the
    server correct no matter how it was launched.
    """
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8")
        except (ValueError, OSError):
            pass


class SemanticMCPServer:
    """Serve the two semantic tools over newline-delimited JSON-RPC."""

    def __init__(self, store_path: str, version: str = ""):
        self.store_path = store_path
        self.version = version
        self.layer = SemanticLayer.load(store_path, version=version or None)

    def dispatch(self, method: str, params: Dict[str, Any]) -> Any:
        if method == "initialize":
            return {
                "protocolVersion": params.get("protocolVersion", "2025-06-18"),
                "capabilities": {"tools": {}, "resources": {}},
                "serverInfo": {"name": "evo-semantic-mcp", "version": "1.0.0"},
            }
        if method == "ping":
            return {}
        if method == "tools/list":
            return {"tools": TOOLS + OPERATIONS}
        if method == "tools/call":
            name = str(params.get("name", ""))
            arguments = params.get("arguments", {})
            if name in {"browse_semantics", "resolve_semantics"}:
                try:
                    semantic_args = dict(arguments or {})
                    requested_workspace = semantic_args.pop("workspace", None)
                    requested_version = str(semantic_args.pop("version", "") or "")
                    if requested_workspace:
                        semantic_workspace = resolve_workspace_for_version(
                            requested_workspace,
                            version=requested_version or "active",
                        )
                        semantic_version = requested_version or None
                    else:
                        semantic_workspace = Path(self.store_path)
                        semantic_version = requested_version or self.version or None
                    self.layer = SemanticLayer.load(
                        str(semantic_workspace), version=semantic_version
                    )
                    result = self.layer.execute(name, semantic_args)
                    result.setdefault("workspace", str(semantic_workspace.resolve()))
                    is_error = False
                except Exception as exc:
                    result = {"status": "error", "message": str(exc)}
                    is_error = True
            elif name in ops._HANDLERS:
                try:
                    result = ops.execute(name, arguments)
                    is_error = False
                except Exception as exc:
                    result = {"status": "error", "message": str(exc)}
                    is_error = True
            else:
                result = {"status": "error", "message": f"Unknown tool: {name}"}
                is_error = True
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, ensure_ascii=False, default=str),
                    }
                ],
                "isError": is_error,
            }
        if method == "resources/list":
            return {
                "resources": [
                    {
                        "uri": _RESOURCE_URI,
                        "name": "EvoOntology semantic session manifest",
                        "mimeType": "text/plain",
                    }
                ]
            }
        if method == "resources/templates/list":
            return {"resourceTemplates": []}
        if method == "resources/read":
            uri = str(params.get("uri", ""))
            if uri != _RESOURCE_URI:
                raise ValueError(f"Unknown resource: {uri}")
            self.layer = SemanticLayer.load(self.store_path, version=self.version or None)
            return {
                "contents": [
                    {
                        "uri": _RESOURCE_URI,
                        "mimeType": "text/plain",
                        "text": self.layer.manifest(),
                    }
                ]
            }
        if method == "shutdown":
            return None
        raise KeyError(method)

    @staticmethod
    def _write(response: Dict[str, Any]) -> None:
        sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
        sys.stdout.flush()

    def run(self) -> None:
        while True:
            try:
                line = sys.stdin.readline()
            except UnicodeDecodeError as exc:
                # Undecodable bytes: report and keep serving; never crash the
                # transport, never reuse a previous request id.
                self._write(
                    {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {"code": PARSE_ERROR, "message": f"Undecodable input: {exc}"},
                    }
                )
                continue
            if not line:
                break
            line = line.strip()
            if not line:
                continue
            request_id: Any = None
            try:
                request = json.loads(line)
                if not isinstance(request, dict):
                    raise ValueError("request must be a JSON object")
                request_id = request.get("id")
                if request_id is None:
                    continue  # notification: no response by design
                result = self.dispatch(str(request.get("method", "")), request.get("params") or {})
                response: Dict[str, Any] = {"jsonrpc": "2.0", "id": request_id, "result": result}
            except json.JSONDecodeError as exc:
                response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": PARSE_ERROR, "message": f"Parse error: {exc}"},
                }
            except KeyError as exc:
                missing = exc.args[0] if exc.args else ""
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": METHOD_NOT_FOUND, "message": f"Method not found: {missing}"},
                }
            except Exception as exc:
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": INTERNAL_ERROR, "message": str(exc)},
                }
            self._write(response)


def main() -> None:
    force_utf8_stdio()
    parser = argparse.ArgumentParser(description="EvoOntology semantic MCP server")
    parser.add_argument(
        "--store",
        default=None,
        help="Workspace root containing active.json (default: <cwd>/.evoontology)",
    )
    parser.add_argument(
        "--version",
        default="",
        help="Explicit semantic version to serve (default: active version)",
    )
    args = parser.parse_args()
    SemanticMCPServer(str(resolve_workspace(args.store)), version=args.version).run()


if __name__ == "__main__":
    main()
