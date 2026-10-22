#!/usr/bin/env python3
"""Validate a session bundle without displaying secret values."""

import argparse
import json
import sys
from pathlib import Path

from session_bundle import SessionBundle, safe_result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origin", required=True)
    parser.add_argument("--profile", default="default")
    parser.add_argument("--auth-home", type=Path)
    args = parser.parse_args()
    try:
        bundle = SessionBundle.load(args.origin, args.profile, args.auth_home)
        print(json.dumps({"valid": True, "directory": str(bundle.directory), "origin": bundle.origin,
                          "profile": bundle.profile, "cookieCount": len(list(bundle.jar)),
                          "headerCount": len(bundle.headers),
                          "expiresAt": bundle.manifest.get("expiresAt")}, ensure_ascii=False))
        return 0
    except Exception as exc:
        print(json.dumps(safe_result(exc), ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
