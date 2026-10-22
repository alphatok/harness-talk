#!/usr/bin/env python3
"""Run a bounded, no-redirect, read-only session probe."""

import argparse
import json
import sys
import urllib.error
from pathlib import Path

from session_bundle import BundleError, SessionBundle, safe_result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origin", required=True)
    parser.add_argument("--profile", default="default")
    parser.add_argument("--auth-home", type=Path)
    parser.add_argument("--url", required=True)
    parser.add_argument("--method", choices=("GET", "HEAD", "POST"), default="GET")
    parser.add_argument("--read-only-post", action="store_true")
    parser.add_argument("--body-file", type=Path)
    parser.add_argument("--content-type")
    parser.add_argument("--expect-status", type=int, action="append")
    parser.add_argument("--expect-text")
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--max-bytes", type=int, default=65536)
    args = parser.parse_args()
    try:
        if args.method == "POST" and (not args.read_only_post or args.body_file is None):
            raise BundleError("POST requires --read-only-post and --body-file")
        if args.method != "POST" and args.body_file is not None:
            raise BundleError("--body-file is only valid with POST")
        if args.max_bytes < 1 or args.max_bytes > 1048576:
            raise BundleError("--max-bytes must be between 1 and 1048576")
        bundle = SessionBundle.load(args.origin, args.profile, args.auth_home)
        data = args.body_file.read_bytes() if args.body_file else None
        if data is not None and len(data) > 1048576:
            raise BundleError("probe request body exceeds 1 MiB")
        if args.content_type:
            bundle.headers["content-type"] = args.content_type
        redirect = False
        try:
            response = bundle.open(args.url, method=args.method, data=data, timeout=args.timeout,
                                   allow_read_only_post=args.read_only_post)
        except urllib.error.HTTPError as error:
            response = error
            redirect = 300 <= error.code < 400
        with response:
            body = response.read(args.max_bytes + 1)
            status = response.getcode()
            content_type = response.headers.get_content_type()
            final_url = response.geturl()
        expected = set(args.expect_status or range(200, 300))
        marker_match = args.expect_text is None or args.expect_text.encode("utf-8") in body
        authenticated = status in expected and marker_match and not redirect and final_url == args.url
        result = {"authenticated": authenticated, "status": status, "finalUrl": final_url,
                  "contentType": content_type, "bytesRead": min(len(body), args.max_bytes),
                  "truncated": len(body) > args.max_bytes, "redirect": redirect,
                  "matchedExpectation": marker_match}
        print(json.dumps(result, ensure_ascii=False))
        return 0 if authenticated else 3
    except Exception as exc:
        print(json.dumps(safe_result(exc), ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
