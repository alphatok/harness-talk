#!/usr/bin/env python3
"""Import one suppressed DevTools request JSON object into a session bundle."""

import argparse
import json
import sys
import termios
import tty
from pathlib import Path

from session_bundle import DEFAULT_TTL_DAYS, safe_result, write_bundle


def read_secret_line() -> str:
    if not sys.stdin.isatty():
        return sys.stdin.readline()
    descriptor = sys.stdin.fileno()
    previous = termios.tcgetattr(descriptor)
    try:
        tty.setraw(descriptor)
        chars = []
        while True:
            char = sys.stdin.read(1)
            if char in {"\n", "\r", ""}:
                break
            chars.append(char)
        return "".join(chars)
    finally:
        termios.tcsetattr(descriptor, termios.TCSADRAIN, previous)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origin", required=True)
    parser.add_argument("--profile", default="default")
    parser.add_argument("--auth-home", type=Path)
    parser.add_argument("--ttl-days", type=int, default=DEFAULT_TTL_DAYS,
                        help=f"local bundle lifetime in days (minimum and default: {DEFAULT_TTL_DAYS})")
    args = parser.parse_args()
    try:
        payload = json.loads(read_secret_line())
        result = write_bundle(origin=args.origin, request_url=payload["requestUrl"],
                              cookie_header=payload["cookie"], headers=payload.get("headers", {}),
                              profile=args.profile, auth_home=args.auth_home, ttl_days=args.ttl_days)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except Exception as exc:
        print(json.dumps(safe_result(exc), ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
