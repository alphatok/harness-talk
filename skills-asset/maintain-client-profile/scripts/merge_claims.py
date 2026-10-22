#!/usr/bin/env python3
"""Validate and propose/apply candidate claims without silently overwriting history."""

from __future__ import annotations

import argparse
import json
import uuid
from pathlib import Path

from client_profile_lib import (
    append_jsonl, client_dir, iter_claim_paths, ledger_path, load_all_claims,
    now_iso, read_jsonl, stable_hash, validate_claim,
)


def load_candidates(path: Path) -> list[dict]:
    if path.suffix == ".jsonl":
        return read_jsonl(path)
    value = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(value, dict) and "claims" in value:
        value = value["claims"]
    if not isinstance(value, list):
        raise ValueError("Candidate file must be a JSON array, {claims: [...]}, or JSONL")
    if not all(isinstance(item, dict) for item in value):
        raise ValueError("Every candidate must be an object")
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--client-id", required=True)
    parser.add_argument("--candidates", required=True, type=Path)
    parser.add_argument("--apply", action="store_true", help="Append accepted claims; default is proposal only")
    args = parser.parse_args()

    root = client_dir(args.workspace, args.client_id)
    if not (root / "client.json").exists():
        raise SystemExit(f"Unknown client: {root}")
    sources = {row["source_id"] for row in read_jsonl(root / "sources" / "index.jsonl")}
    existing = load_all_claims(root)
    existing_ids = {row.get("claim_id") for row in existing}
    existing_fingerprints = {
        stable_hash({k: row.get(k) for k in ("client_id", "scope", "subject", "predicate", "value", "claim_type", "source_refs")})
        for row in existing
    }
    proposals = []
    accepted_by_ledger: dict[Path, list[dict]] = {}
    for candidate in load_candidates(args.candidates):
        claim = dict(candidate)
        claim.setdefault("claim_id", f"clm-{uuid.uuid4().hex[:12]}")
        claim.setdefault("client_id", args.client_id)
        claim.setdefault("scope", {"type": "client"})
        claim.setdefault("status", "unverified")
        claim.setdefault("confidence", 0.5)
        claim.setdefault("source_refs", [])
        claim.setdefault("observed_at", now_iso())
        claim.setdefault("sensitivity", "internal")
        claim.setdefault("review", {"state": "pending", "owner": "User"})
        errors = validate_claim(claim, args.client_id)
        missing_sources = [source_id for source_id in claim.get("source_refs", []) if source_id not in sources]
        if missing_sources:
            errors.append(f"unknown source_refs: {missing_sources}")
        fingerprint = stable_hash({k: claim.get(k) for k in ("client_id", "scope", "subject", "predicate", "value", "claim_type", "source_refs")})
        if claim["claim_id"] in existing_ids:
            errors.append("duplicate claim_id")
        if fingerprint in existing_fingerprints:
            errors.append("duplicate semantic claim")
        action = "reject" if errors else "append"
        proposals.append({"claim_id": claim["claim_id"], "action": action, "errors": errors, "claim": claim})
        if not errors:
            accepted_by_ledger.setdefault(ledger_path(root, claim), []).append(claim)
            existing_ids.add(claim["claim_id"])
            existing_fingerprints.add(fingerprint)

    summary = {
        "mode": "apply" if args.apply else "propose",
        "accepted": sum(1 for item in proposals if item["action"] == "append"),
        "rejected": sum(1 for item in proposals if item["action"] == "reject"),
        "proposals": proposals,
    }
    if args.apply:
        for path, rows in accepted_by_ledger.items():
            if path.parent.name in {"opportunities", "projects"}:
                raise AssertionError("Unexpected scope path")
            if "opportunities" in path.parts or "projects" in path.parts:
                scope_root = path.parent
                if not scope_root.exists():
                    raise SystemExit(f"Scope directory does not exist: {scope_root}")
            append_jsonl(path, rows)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if summary["rejected"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
