#!/usr/bin/env python3
"""Deterministic local end-to-end test for capture, load, and read-only probe."""

import http.server
import datetime as dt
import json
import stat
import tempfile
import threading
from pathlib import Path

from session_bundle import BundleError, SessionBundle, write_bundle


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        valid = "session=ok" in (self.headers.get("Cookie") or "") and self.headers.get("X-Context") == "demo"
        body = b'{"authenticated":true}' if valid else b'{"authenticated":false}'
        self.send_response(200 if valid else 401)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        pass


def main() -> int:
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    origin = f"http://127.0.0.1:{server.server_port}"
    try:
        with tempfile.TemporaryDirectory(prefix="httpweb-auth-test-") as temporary:
            root = Path(temporary) / "auth"
            result = write_bundle(origin=origin, request_url=f"{origin}/api/me",
                                  cookie_header="session=ok; theme=dark",
                                  headers={"X-Context": "demo", "Sec-Fetch-Site": "same-origin", "Cookie": "ignored"},
                                  auth_home=root)
            bundle = SessionBundle.load(origin, auth_home=root)
            expires_at = dt.datetime.fromisoformat(result["expiresAt"].replace("Z", "+00:00"))
            remaining = expires_at - dt.datetime.now(dt.timezone.utc)
            response = bundle.open(f"{origin}/api/me")
            with response:
                body, status = response.read(1024), response.getcode()
            refused = False
            try:
                bundle.headers_for("http://example.invalid/api/me")
            except BundleError:
                refused = True
            minimum_refused = False
            try:
                write_bundle(origin=origin, request_url=f"{origin}/api/me", cookie_header="session=ok",
                             headers={}, auth_home=root, profile="too-short", ttl_days=6)
            except BundleError:
                minimum_refused = True
            expired_result = write_bundle(origin=origin, request_url=f"{origin}/api/me",
                                          cookie_header="session=ok", headers={}, auth_home=root,
                                          profile="expired")
            expired_manifest_path = Path(expired_result["directory"]) / "manifest.json"
            expired_manifest = json.loads(expired_manifest_path.read_text(encoding="utf-8"))
            expired_manifest["expiresAt"] = "2000-01-01T00:00:00Z"
            expired_manifest_path.write_text(json.dumps(expired_manifest), encoding="utf-8")
            expired_manifest_path.chmod(0o600)
            expired_refused = False
            try:
                SessionBundle.load(origin, profile="expired", auth_home=root)
            except BundleError:
                expired_refused = True
            files_private = all(stat.S_IMODE(path.stat().st_mode) == 0o600 for path in bundle.directory.iterdir())
            dirs_private = all(stat.S_IMODE(path.stat().st_mode) == 0o700 for path in (root, bundle.directory.parent, bundle.directory))
            passed = all((status == 200, b'"authenticated":true' in body, refused, files_private,
                          dirs_private, "sec-fetch-site" not in bundle.headers, result["cookieCount"] == 2,
                          result["ttlDays"] == 7, remaining >= dt.timedelta(days=6, hours=23),
                          all(cookie.expires and cookie.expires >= int(expires_at.timestamp()) - 1
                              for cookie in bundle.jar), minimum_refused, expired_refused))
            print(json.dumps({"passed": passed, "capture": True, "load": True,
                              "readOnlyProbe": status == 200, "crossOriginRefused": refused,
                              "privatePermissions": files_private and dirs_private}, ensure_ascii=False))
            return 0 if passed else 1
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
