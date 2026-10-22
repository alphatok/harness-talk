#!/usr/bin/env python3
"""Secure, same-origin HTTP session bundle helpers (stdlib only)."""

from __future__ import annotations

import datetime as dt
import http.cookiejar
import json
import os
import re
import stat
import tempfile
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

FORMAT_VERSION = 1
MIN_TTL_DAYS = 7
DEFAULT_TTL_DAYS = 7
PROFILE_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
COOKIE_NAME_RE = re.compile(r"^[!#$%&'*+.^_`|~0-9A-Za-z-]+$")
DENY_HEADERS = {
    "accept-encoding", "connection", "content-length", "cookie", "date",
    "host", "keep-alive", "te", "traceid", "trailer", "transfer-encoding", "upgrade",
}
DENY_PREFIXES = ("proxy-", "sec-", ":")
MAX_HEADERS = 128
MAX_HEADER_VALUE = 8192
MAX_HEADER_TOTAL = 65536


class BundleError(ValueError):
    pass


def default_auth_home() -> Path:
    configured = os.environ.get("HTTPWEB_AUTH_HOME")
    return Path(configured).expanduser() if configured else Path.home() / "httpweb_auth"


def normalize_origin(origin: str) -> tuple[str, str, str, int | None]:
    parsed = urllib.parse.urlsplit(origin)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise BundleError("origin must be an absolute http(s) origin")
    if parsed.username or parsed.password or parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
        raise BundleError("origin must contain only scheme, host, and optional port")
    host = parsed.hostname.lower()
    port = parsed.port
    default_port = 80 if parsed.scheme == "http" else 443
    netloc = host if port in {None, default_port} else f"{host}:{port}"
    return f"{parsed.scheme}://{netloc}", parsed.scheme, host, port


def origin_of(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise BundleError("request URL must be absolute http(s)")
    host = parsed.hostname.lower()
    default_port = 80 if parsed.scheme == "http" else 443
    netloc = host if parsed.port in {None, default_port} else f"{host}:{parsed.port}"
    return f"{parsed.scheme}://{netloc}"


def validate_profile(profile: str) -> str:
    if profile in {".", ".."} or not PROFILE_RE.fullmatch(profile):
        raise BundleError("invalid profile; use 1-64 letters, digits, dot, underscore, or hyphen")
    return profile


def host_key(origin: str) -> str:
    normalized, scheme, host, port = normalize_origin(origin)
    default_port = 80 if scheme == "http" else 443
    return host if port in {None, default_port} else f"{host}__{port}"


def bundle_path(origin: str, profile: str = "default", auth_home: Path | None = None) -> Path:
    return (auth_home or default_auth_home()).expanduser() / host_key(origin) / validate_profile(profile)


def _ensure_private_dir(path: Path, create: bool = False) -> None:
    if create:
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
    if path.is_symlink() or not path.is_dir():
        raise BundleError(f"unsafe bundle directory: {path}")
    info = path.stat()
    if info.st_uid != os.getuid():
        raise BundleError(f"bundle directory is not owned by current user: {path}")
    if stat.S_IMODE(info.st_mode) & 0o077:
        raise BundleError(f"bundle directory permissions are too broad: {path}")


def _ensure_private_tree(path: Path) -> None:
    pending: list[Path] = []
    current = path
    while not current.exists():
        pending.append(current)
        current = current.parent
    for directory in reversed(pending):
        directory.mkdir(mode=0o700)
    for directory in (path.parent.parent, path.parent, path):
        _ensure_private_dir(directory)


def _check_private_file(path: Path) -> None:
    if path.is_symlink() or not path.is_file():
        raise BundleError(f"unsafe or missing bundle file: {path}")
    info = path.stat()
    if info.st_uid != os.getuid():
        raise BundleError(f"bundle file is not owned by current user: {path}")
    if stat.S_IMODE(info.st_mode) & 0o077:
        raise BundleError(f"bundle file permissions are too broad: {path}")


def _atomic_write(path: Path, content: str) -> None:
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def _header_allowed(name: str) -> bool:
    lowered = name.strip().lower()
    return bool(lowered) and lowered not in DENY_HEADERS and not lowered.startswith(DENY_PREFIXES)


def filter_headers(headers: Mapping[str, Any]) -> dict[str, str]:
    if len(headers) > MAX_HEADERS:
        raise BundleError("too many request headers")
    clean: dict[str, str] = {}
    total = 0
    for raw_name, raw_value in headers.items():
        name = str(raw_name).strip().lower()
        value = str(raw_value).strip()
        if not _header_allowed(name) or not value:
            continue
        if "\r" in value or "\n" in value or len(value) > MAX_HEADER_VALUE:
            raise BundleError(f"unsafe header value for {name}")
        total += len(name) + len(value)
        if total > MAX_HEADER_TOTAL:
            raise BundleError("request headers exceed size limit")
        clean[name] = value
    return dict(sorted(clean.items()))


def parse_cookie_header(cookie_header: str) -> list[tuple[str, str]]:
    if not isinstance(cookie_header, str) or not cookie_header.strip():
        raise BundleError("cookie header is empty")
    cookies: list[tuple[str, str]] = []
    for item in cookie_header.split(";"):
        item = item.strip()
        if not item or "=" not in item:
            continue
        name, value = item.split("=", 1)
        name, value = name.strip(), value.strip()
        if not COOKIE_NAME_RE.fullmatch(name) or any(char in value for char in "\r\n\t"):
            raise BundleError("cookie header contains an invalid cookie")
        cookies.append((name, value))
    if not cookies:
        raise BundleError("no valid cookies found")
    return cookies


def _cookie_jar_text(host: str, secure: bool, cookies: list[tuple[str, str]], expires_at: dt.datetime) -> str:
    lines = ["# Netscape HTTP Cookie File", "# Generated from an authenticated request; values are secrets."]
    for name, value in cookies:
        lines.append("\t".join([host, "FALSE", "/", "TRUE" if secure else "FALSE",
                                str(int(expires_at.timestamp())), name, value]))
    return "\n".join(lines) + "\n"


def _parse_utc_timestamp(value: Any, field: str) -> dt.datetime:
    if not isinstance(value, str):
        raise BundleError(f"manifest {field} is missing or invalid")
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise BundleError(f"manifest {field} is missing or invalid") from exc
    if parsed.tzinfo is None:
        raise BundleError(f"manifest {field} must include a timezone")
    return parsed.astimezone(dt.timezone.utc)


def write_bundle(*, origin: str, request_url: str, cookie_header: str,
                 headers: Mapping[str, Any], profile: str = "default",
                 auth_home: Path | None = None,
                 source: str = "chrome-devtools-successful-request",
                 ttl_days: int = DEFAULT_TTL_DAYS) -> dict[str, Any]:
    normalized, scheme, host, _ = normalize_origin(origin)
    if origin_of(request_url) != normalized:
        raise BundleError("request URL origin does not match declared origin")
    profile = validate_profile(profile)
    if isinstance(ttl_days, bool) or not isinstance(ttl_days, int) or ttl_days < MIN_TTL_DAYS:
        raise BundleError(f"ttl_days must be an integer of at least {MIN_TTL_DAYS}")
    cookies = parse_cookie_header(cookie_header)
    reusable = filter_headers(headers)
    directory = bundle_path(normalized, profile, auth_home)
    _ensure_private_tree(directory)
    captured_at = dt.datetime.now(dt.timezone.utc)
    expires_at = captured_at + dt.timedelta(days=ttl_days)
    manifest = {
        "formatVersion": FORMAT_VERSION, "origin": normalized, "hostKey": host_key(normalized),
        "profile": profile, "capturedAt": captured_at.isoformat().replace("+00:00", "Z"),
        "expiresAt": expires_at.isoformat().replace("+00:00", "Z"), "ttlDays": ttl_days,
        "source": source, "cookieCount": len(cookies),
        "headerNames": list(reusable), "files": {"cookies": "cookies.txt", "headers": "headers.json"},
    }
    _atomic_write(directory / "cookies.txt", _cookie_jar_text(host, scheme == "https", cookies, expires_at))
    _atomic_write(directory / "headers.json", json.dumps(reusable, ensure_ascii=False, indent=2) + "\n")
    _atomic_write(directory / "manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return {"written": True, "directory": str(directory), "origin": normalized, "profile": profile,
            "cookieCount": len(cookies), "headerCount": len(reusable),
            "expiresAt": manifest["expiresAt"], "ttlDays": ttl_days}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


@dataclass
class SessionBundle:
    origin: str
    profile: str
    directory: Path
    headers: dict[str, str]
    jar: http.cookiejar.MozillaCookieJar
    manifest: dict[str, Any]

    @classmethod
    def load(cls, origin: str, profile: str = "default", auth_home: Path | None = None) -> "SessionBundle":
        normalized, _, _, _ = normalize_origin(origin)
        directory = bundle_path(normalized, profile, auth_home)
        _ensure_private_dir(directory)
        for name in ("cookies.txt", "headers.json", "manifest.json"):
            _check_private_file(directory / name)
        manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
        if manifest.get("formatVersion") != FORMAT_VERSION or manifest.get("origin") != normalized:
            raise BundleError("manifest version or origin mismatch")
        if manifest.get("profile") != validate_profile(profile):
            raise BundleError("manifest profile mismatch")
        captured_at = _parse_utc_timestamp(manifest.get("capturedAt"), "capturedAt")
        expires_at_value = manifest.get("expiresAt")
        legacy_session_cookies = expires_at_value is None
        expires_at = (_parse_utc_timestamp(expires_at_value, "expiresAt") if expires_at_value is not None
                      else captured_at + dt.timedelta(days=DEFAULT_TTL_DAYS))
        if expires_at <= dt.datetime.now(dt.timezone.utc):
            raise BundleError("session bundle has expired; capture a fresh successful request")
        headers_raw = json.loads((directory / "headers.json").read_text(encoding="utf-8"))
        if not isinstance(headers_raw, dict):
            raise BundleError("headers.json must contain an object")
        headers = filter_headers(headers_raw)
        jar = http.cookiejar.MozillaCookieJar(str(directory / "cookies.txt"))
        jar.load(ignore_discard=True, ignore_expires=legacy_session_cookies)
        if legacy_session_cookies:
            for cookie in jar:
                if cookie.expires == 0:
                    cookie.expires = None
        return cls(normalized, profile, directory, headers, jar, manifest)

    def headers_for(self, url: str) -> dict[str, str]:
        if origin_of(url) != self.origin:
            raise BundleError("cross-origin session replay refused")
        request = urllib.request.Request(url)
        self.jar.add_cookie_header(request)
        combined = dict(self.headers)
        cookie = request.get_header("Cookie")
        if cookie:
            combined["cookie"] = cookie
        return combined

    def open(self, url: str, *, method: str = "GET", data: bytes | None = None,
             timeout: float = 10.0, allow_read_only_post: bool = False):
        method = method.upper()
        if method not in {"GET", "HEAD"} and not (method == "POST" and allow_read_only_post):
            raise BundleError("method refused; only GET/HEAD or explicit read-only POST are allowed")
        request = urllib.request.Request(url, data=data, headers=self.headers_for(url), method=method)
        opener = urllib.request.build_opener(NoRedirect(), urllib.request.HTTPCookieProcessor(self.jar))
        return opener.open(request, timeout=timeout)


def safe_result(error: Exception) -> dict[str, Any]:
    return {"ok": False, "error": type(error).__name__, "message": str(error)}
