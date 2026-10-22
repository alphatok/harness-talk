#!/usr/bin/env python3
"""Evaluate field-level freshness without deleting stale information."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from client_profile_lib import client_dir, find_ttl, load_json, parse_date, write_json


def walk_packets(node: object, path: str = ""):
    if isinstance(node, dict):
        if "claim_refs" in node and "as_of" in node:
            yield path, node
        else:
            for key, value in node.items():
                next_path = f"{path}.{key}" if path else key
                yield from walk_packets(value, next_path)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from walk_packets(value, f"{path}[{index}]")


def evaluate(profile: dict, policy: dict) -> dict:
    counts = {"current": 0, "attention": 0, "stale": 0, "unknown": 0}
    today = date.today()
    for path, packet in walk_packets(profile):
        as_of = parse_date(packet.get("as_of"))
        expires_at = parse_date(packet.get("expires_at"))
        ttl = find_ttl(path, policy)
        if not as_of:
            freshness = "unknown"
            age_days = None
        else:
            age_days = (today - as_of).days
            if expires_at and today > expires_at:
                freshness = "stale"
            elif age_days > ttl:
                freshness = "stale"
            elif age_days > round(ttl * float(policy.get("attention_ratio", 0.75))):
                freshness = "attention"
            else:
                freshness = "current"
        packet["freshness"] = freshness
        packet["age_days"] = age_days
        packet["ttl_days"] = ttl
        counts[freshness] += 1
    if counts["stale"]:
        overall = "stale"
    elif counts["attention"]:
        overall = "attention"
    elif counts["current"]:
        overall = "current"
    else:
        overall = "unknown"
    profile.setdefault("profile_meta", {})["overall_freshness"] = overall
    return counts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--client-id", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    root = client_dir(args.workspace, args.client_id)
    policy = load_json(args.workspace.resolve() / "policies" / "freshness-policy.json")
    profile_paths = [root / "profile" / "current.json"]
    profile_paths.extend(root.joinpath("opportunities").glob("*/profile.json"))
    profile_paths.extend(root.joinpath("projects").glob("*/profile.json"))
    report = {}
    for path in profile_paths:
        if not path.exists():
            continue
        profile = load_json(path)
        report[str(path.relative_to(root))] = evaluate(profile, policy)
        if args.apply:
            write_json(path, profile)
    print(json.dumps({"mode": "apply" if args.apply else "check", "profiles": report}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
