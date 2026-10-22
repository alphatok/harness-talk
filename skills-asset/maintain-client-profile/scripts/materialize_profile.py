#!/usr/bin/env python3
"""Materialize current client/opportunity/project snapshots from append-only claims."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from client_profile_lib import (
    claim_key, claim_rank, client_dir, load_all_claims, load_json, now_iso,
    set_nested, stable_hash, write_json,
)


def packet(claim: dict, status: str | None = None) -> dict:
    return {
        "value": claim["value"],
        "status": status or claim["status"],
        "confidence": claim["confidence"],
        "claim_type": claim["claim_type"],
        "claim_refs": [claim["claim_id"]],
        "source_refs": claim.get("source_refs", []),
        "as_of": claim.get("effective_at") or claim.get("observed_at"),
        "expires_at": claim.get("expires_at"),
        "owner": claim.get("owner") or claim.get("review", {}).get("owner"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--client-id", required=True)
    args = parser.parse_args()
    root = client_dir(args.workspace, args.client_id)
    client = load_json(root / "client.json")
    claims = load_all_claims(root)
    superseded_ids = {item for claim in claims for item in claim.get("supersedes", [])}
    active = [
        claim for claim in claims
        if claim["claim_id"] not in superseded_ids and claim.get("status") not in {"rejected", "disputed", "superseded"}
    ]
    grouped: dict[tuple, list[dict]] = defaultdict(list)
    for claim in active:
        grouped[claim_key(claim)].append(claim)

    client_profile = {
        "schema_version": "1.0.0",
        "profile_meta": {
            "client_id": args.client_id, "display_name": client["display_name"],
            "owner": client["owner"], "updated_at": now_iso(),
            "overall_freshness": "unknown", "claim_count": len(active),
        },
        "organization": {}, "relationships": {}, "current_state": {},
        "needs_and_value": {}, "delivery_readiness": {}, "sales_strategy": {},
    }
    scoped_profiles: dict[tuple[str, str], dict] = {}
    conflicts = []
    for key, candidates in grouped.items():
        candidates.sort(key=claim_rank, reverse=True)
        selected = candidates[0]
        same_rank = [item for item in candidates if claim_rank(item)[:2] == claim_rank(selected)[:2]]
        different = {stable_hash(item["value"]) for item in same_rank}
        explicitly_replaced = set(selected.get("supersedes", []))
        is_conflict = len(different) > 1 and not any(item["claim_id"] in explicitly_replaced for item in candidates[1:])
        value_packet = packet(selected, "conflicted" if is_conflict else None)
        if is_conflict:
            value_packet["alternatives"] = [packet(item) for item in same_rank]
            conflicts.append({"scope": selected["scope"], "subject": selected["subject"], "predicate": selected["predicate"], "claim_refs": [item["claim_id"] for item in same_rank]})
        scope_type, scope_id, _, predicate = key
        if scope_type == "client":
            set_nested(client_profile, predicate, value_packet)
        else:
            profile = scoped_profiles.setdefault((scope_type, scope_id), {"schema_version": "1.0.0", "profile_meta": {"client_id": args.client_id, "scope_type": scope_type, "scope_id": scope_id, "updated_at": now_iso()}, "current_claims": {}})
            set_nested(profile["current_claims"], predicate, value_packet)

    write_json(root / "profile" / "current.json", client_profile)
    write_json(root / "reviews" / "conflicts.json", {"updated_at": now_iso(), "conflicts": conflicts})
    for (scope_type, scope_id), profile in scoped_profiles.items():
        collection = "opportunities" if scope_type == "opportunity" else "projects"
        scope_root = root / collection / scope_id
        if scope_root.exists():
            write_json(scope_root / "profile.json", profile)
    print(json.dumps({"active_claims": len(active), "conflicts": len(conflicts), "scoped_profiles": len(scoped_profiles)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
