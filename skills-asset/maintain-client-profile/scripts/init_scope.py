#!/usr/bin/env python3
"""Create an opportunity or delivery project under an existing client."""

from __future__ import annotations

import argparse
from pathlib import Path

from client_profile_lib import client_dir, now_iso, require_slug, write_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--client-id", required=True)
    parser.add_argument("--type", required=True, choices=("opportunity", "project"))
    parser.add_argument("--id", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--owner", default="User")
    parser.add_argument("--origin-opportunity")
    args = parser.parse_args()

    scope_id = require_slug(args.id, "scope id")
    root = client_dir(args.workspace, args.client_id)
    if not (root / "client.json").exists():
        raise SystemExit(f"Unknown client: {root}")
    collection = "opportunities" if args.type == "opportunity" else "projects"
    scope_root = root / collection / scope_id
    if scope_root.exists():
        raise SystemExit(f"Scope already exists: {scope_root}")
    for folder in ("interactions", "deliverables", "views", "changes"):
        (scope_root / folder).mkdir(parents=True, exist_ok=True)
    if args.type == "project":
        for folder in ("requirements", "decisions", "meetings", "acceptance", "closure", "sources"):
            (scope_root / folder).mkdir(parents=True, exist_ok=True)
    timestamp = now_iso()
    data = {
        "schema_version": "1.0.0", "client_id": args.client_id, f"{args.type}_id": scope_id,
        "name": args.name, "owner": args.owner,
        "status": "discovery" if args.type == "opportunity" else "planned",
        "created_at": timestamp, "updated_at": timestamp,
    }
    if args.origin_opportunity:
        data["origin_opportunity"] = args.origin_opportunity
    write_json(scope_root / f"{args.type}.json", data)
    write_json(scope_root / "profile.json", {"profile_meta": data, "current_claims": {}})
    (scope_root / "claims.jsonl").touch()
    print(f"Created {args.type}: {scope_root}")


if __name__ == "__main__":
    main()
