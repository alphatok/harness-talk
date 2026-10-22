#!/usr/bin/env python3
"""Migrate an existing private cookie jar and headers JSON into this bundle format."""

import argparse
import http.cookiejar
import json
import os
import stat
import sys
from pathlib import Path

from session_bundle import BundleError, DEFAULT_TTL_DAYS, safe_result, write_bundle


def private_regular_file(path: Path) -> None:
    if path.is_symlink() or not path.is_file():
        raise BundleError(f"unsafe or missing source file: {path}")
    info = path.stat()
    if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
        raise BundleError(f"source credential file must be owned by current user and mode 0600: {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origin", required=True)
    parser.add_argument("--profile", default="default")
    parser.add_argument("--auth-home", type=Path)
    parser.add_argument("--cookie-file", type=Path, required=True)
    parser.add_argument("--headers-file", type=Path, required=True)
    parser.add_argument("--ttl-days", type=int, default=DEFAULT_TTL_DAYS,
                        help=f"local bundle lifetime in days (minimum and default: {DEFAULT_TTL_DAYS})")
    args = parser.parse_args()
    try:
        private_regular_file(args.cookie_file)
        private_regular_file(args.headers_file)
        jar = http.cookiejar.MozillaCookieJar(str(args.cookie_file))
        jar.load(ignore_discard=True, ignore_expires=True)
        pairs = [(cookie.name, cookie.value) for cookie in jar]
        if not pairs:
            raise BundleError("source cookie jar is empty")
        headers = json.loads(args.headers_file.read_text(encoding="utf-8"))
        if not isinstance(headers, dict):
            raise BundleError("source headers file must contain an object")
        result = write_bundle(origin=args.origin, request_url=f"{args.origin.rstrip('/')}/",
                              cookie_header="; ".join(f"{name}={value}" for name, value in pairs),
                              headers=headers, profile=args.profile, auth_home=args.auth_home,
                              source="private-legacy-session-bundle", ttl_days=args.ttl_days)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except Exception as exc:
        print(json.dumps(safe_result(exc), ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
