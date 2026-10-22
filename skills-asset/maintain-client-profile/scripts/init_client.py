#!/usr/bin/env python3
"""Create one durable client directory inside a profile workspace."""

from __future__ import annotations

import argparse
from pathlib import Path

from client_profile_lib import client_dir, load_json, now_iso, require_slug, write_json
from init_workspace import initialize


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--client-id", required=True)
    parser.add_argument("--display-name", required=True)
    parser.add_argument("--owner", default="User")
    parser.add_argument("--aliases", nargs="*", default=[])
    args = parser.parse_args()

    client_id = require_slug(args.client_id, "client_id")
    initialize(args.workspace, args.owner)
    root = client_dir(args.workspace, client_id)
    if (root / "client.json").exists():
        raise SystemExit(f"Client already exists: {root}")
    for folder in (
        "profile", "claims", "stakeholders", "interactions", "research", "sources/originals",
        "opportunities", "projects", "reviews", "views", "changes", "archive",
    ):
        (root / folder).mkdir(parents=True, exist_ok=True)
    created_at = now_iso()
    write_json(root / "client.json", {
        "schema_version": "1.0.0",
        "client_id": client_id,
        "display_name": args.display_name,
        "aliases": args.aliases,
        "owner": args.owner,
        "status": "active",
        "created_at": created_at,
        "updated_at": created_at,
    })
    write_json(root / "profile" / "current.json", {
        "schema_version": "1.0.0",
        "profile_meta": {
            "client_id": client_id,
            "display_name": args.display_name,
            "owner": args.owner,
            "updated_at": created_at,
            "overall_freshness": "unknown",
        },
        "organization": {}, "relationships": {}, "current_state": {},
        "needs_and_value": {}, "delivery_readiness": {}, "sales_strategy": {},
    })
    write_json(root / "profile" / "completeness.json", {"score": 0, "missing_critical_fields": [], "updated_at": created_at})
    write_json(root / "stakeholders" / "index.json", {"stakeholders": []})
    write_json(root / "reviews" / "pending-claims.json", {"claims": []})
    write_json(root / "reviews" / "conflicts.json", {"conflicts": []})
    for ledger in ("organization", "relationships", "environment", "needs-and-value", "sales-strategy", "corrections"):
        (root / "claims" / f"{ledger}.jsonl").touch()
    (root / "sources" / "index.jsonl").touch()

    registry_path = args.workspace.resolve() / "registry" / "clients.json"
    registry = load_json(registry_path, {"clients": []})
    registry["clients"].append({"client_id": client_id, "display_name": args.display_name, "owner": args.owner, "status": "active"})
    write_json(registry_path, registry)
    print(f"Created client: {root}")


if __name__ == "__main__":
    main()
