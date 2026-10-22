#!/usr/bin/env python3
"""Initialize a client-profile workspace with schemas and governance defaults."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from client_profile_lib import now_iso, write_json


def initialize(workspace: Path, owner: str) -> None:
    skill_root = Path(__file__).resolve().parent.parent
    workspace = workspace.resolve()
    for folder in ("clients", "schemas", "policies", "templates/client", "templates/opportunity", "templates/project", "registry"):
        (workspace / folder).mkdir(parents=True, exist_ok=True)
    for schema in skill_root.joinpath("references").glob("*.schema.json"):
        shutil.copy2(schema, workspace / "schemas" / schema.name)
    for policy in ("evidence-policy.json", "freshness-policy.json", "sensitivity-policy.json"):
        shutil.copy2(skill_root / "references" / policy, workspace / "policies" / policy)
    workspace_file = workspace / "workspace.json"
    if not workspace_file.exists():
        write_json(workspace_file, {
            "schema_version": "1.0.0",
            "created_at": now_iso(),
            "owner": owner,
            "default_update_mode": "propose",
        })
    registry = workspace / "registry" / "clients.json"
    if not registry.exists():
        write_json(registry, {"clients": []})
    print(f"Initialized workspace: {workspace}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--owner", default="User")
    args = parser.parse_args()
    initialize(args.workspace, args.owner)


if __name__ == "__main__":
    main()
