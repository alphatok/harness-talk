#!/usr/bin/env python3
"""Validate directory integrity, JSON/JSONL records, IDs, and source references."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from client_profile_lib import client_dir, iter_claim_paths, load_json, read_jsonl, validate_claim


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--client-id", required=True)
    args = parser.parse_args()
    root = client_dir(args.workspace, args.client_id)
    errors = []
    required = ["client.json", "profile/current.json", "sources/index.jsonl", "reviews/conflicts.json"]
    for item in required:
        if not (root / item).exists():
            errors.append(f"missing {item}")
    if errors:
        print(json.dumps({"valid": False, "errors": errors}, ensure_ascii=False, indent=2))
        raise SystemExit(1)
    client = load_json(root / "client.json")
    source_rows = read_jsonl(root / "sources" / "index.jsonl")
    source_ids = [row.get("source_id") for row in source_rows]
    duplicate_sources = sorted({value for value in source_ids if source_ids.count(value) > 1})
    if duplicate_sources:
        errors.append(f"duplicate source ids: {duplicate_sources}")
    claim_ids = []
    for path in iter_claim_paths(root):
        for number, claim in enumerate(read_jsonl(path), start=1):
            claim_ids.append(claim.get("claim_id"))
            for error in validate_claim(claim, client["client_id"]):
                errors.append(f"{path.relative_to(root)}:{number}: {error}")
            for source_id in claim.get("source_refs", []):
                if source_id not in source_ids:
                    errors.append(f"{path.relative_to(root)}:{number}: unknown source {source_id}")
    duplicate_claims = sorted({value for value in claim_ids if value and claim_ids.count(value) > 1})
    if duplicate_claims:
        errors.append(f"duplicate claim ids: {duplicate_claims}")
    result = {"valid": not errors, "client_id": client["client_id"], "sources": len(source_rows), "claims": len(claim_ids), "errors": errors}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
