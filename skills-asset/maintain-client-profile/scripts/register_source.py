#!/usr/bin/env python3
"""Register a source and optionally preserve a local original under the client."""

from __future__ import annotations

import argparse
import shutil
import uuid
from pathlib import Path

from client_profile_lib import append_jsonl, client_dir, now_iso, read_jsonl, sha256_file


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--client-id", required=True)
    parser.add_argument("--type", required=True, choices=("public_research", "meeting_minutes", "transcript", "image", "email", "document", "manual_correction", "system_export", "other"))
    parser.add_argument("--title", required=True)
    parser.add_argument("--path", type=Path)
    parser.add_argument("--uri")
    parser.add_argument("--provider", default="unknown")
    parser.add_argument("--event-at")
    parser.add_argument("--authority", default="unknown")
    parser.add_argument("--sensitivity", default="internal", choices=("public", "internal", "confidential", "restricted"))
    parser.add_argument("--copy-original", action="store_true")
    args = parser.parse_args()

    root = client_dir(args.workspace, args.client_id)
    if not (root / "client.json").exists():
        raise SystemExit(f"Unknown client: {root}")
    if not args.path and not args.uri:
        raise SystemExit("Provide --path or --uri")
    source_id = f"src-{uuid.uuid4().hex[:12]}"
    uri = args.uri
    content_hash = None
    if args.path:
        source_path = args.path.resolve()
        if not source_path.is_file():
            raise SystemExit(f"Source file does not exist: {source_path}")
        content_hash = sha256_file(source_path)
        uri = str(source_path)
        if args.copy_original:
            target = root / "sources" / "originals" / f"{source_id}-{source_path.name}"
            shutil.copy2(source_path, target)
            uri = str(target.relative_to(root))
    record = {
        "source_id": source_id,
        "client_id": args.client_id,
        "type": args.type,
        "title": args.title,
        "uri": uri,
        "content_hash": content_hash,
        "captured_at": now_iso(),
        "event_at": args.event_at,
        "provider": args.provider,
        "authority": args.authority,
        "sensitivity": args.sensitivity,
    }
    existing = read_jsonl(root / "sources" / "index.jsonl")
    duplicate = next((item for item in existing if content_hash and item.get("content_hash") == content_hash), None)
    if duplicate:
        print(f"Duplicate content already registered as {duplicate['source_id']}")
        return
    append_jsonl(root / "sources" / "index.jsonl", [record])
    print(source_id)


if __name__ == "__main__":
    main()
