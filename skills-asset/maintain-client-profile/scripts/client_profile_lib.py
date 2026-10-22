#!/usr/bin/env python3
"""Shared, dependency-free helpers for maintain-client-profile scripts."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable


CLAIM_TYPES = {
    "verified_fact",
    "customer_statement",
    "supplier_evidence",
    "internal_observation",
    "inference",
    "hypothesis",
    "correction",
}
CLAIM_STATUSES = {
    "confirmed",
    "probable",
    "unverified",
    "conflicted",
    "disputed",
    "stale",
    "superseded",
    "rejected",
}
SCOPE_TYPES = {"client", "opportunity", "project"}
SENSITIVITY_LEVELS = {"public", "internal", "confidential", "restricted"}


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().replace(microsecond=0).isoformat()


def today_iso() -> str:
    return date.today().isoformat()


def require_slug(value: str, label: str) -> str:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,62}[a-z0-9]", value):
        raise ValueError(f"{label} must be 3-64 lowercase letters, digits, or hyphens: {value!r}")
    return value


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        if default is not None:
            return default
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{number}: {exc}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"JSONL row must be an object at {path}:{number}")
            rows.append(value)
    return rows


def append_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")))
            handle.write("\n")


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    text = value[:10]
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def client_dir(workspace: Path, client_id: str) -> Path:
    return workspace.resolve() / "clients" / require_slug(client_id, "client_id")


def ledger_path(client_root: Path, claim: dict[str, Any]) -> Path:
    scope = claim["scope"]["type"]
    if scope == "opportunity":
        return client_root / "opportunities" / claim["scope"]["id"] / "claims.jsonl"
    if scope == "project":
        return client_root / "projects" / claim["scope"]["id"] / "claims.jsonl"
    domain = claim.get("domain", "organization")
    if domain not in {"organization", "relationships", "environment", "needs-and-value", "sales-strategy"}:
        domain = "organization"
    return client_root / "claims" / f"{domain}.jsonl"


def iter_claim_paths(client_root: Path) -> list[Path]:
    paths = sorted((client_root / "claims").glob("*.jsonl"))
    paths.extend(sorted((client_root / "opportunities").glob("*/claims.jsonl")))
    paths.extend(sorted((client_root / "projects").glob("*/claims.jsonl")))
    return paths


def load_all_claims(client_root: Path) -> list[dict[str, Any]]:
    claims: list[dict[str, Any]] = []
    for path in iter_claim_paths(client_root):
        claims.extend(read_jsonl(path))
    return claims


def validate_claim(claim: dict[str, Any], expected_client_id: str | None = None) -> list[str]:
    errors: list[str] = []
    required = ["claim_id", "client_id", "scope", "subject", "predicate", "value", "claim_type", "status", "confidence", "source_refs", "observed_at", "sensitivity"]
    for key in required:
        if key not in claim:
            errors.append(f"missing {key}")
    if errors:
        return errors
    if expected_client_id and claim["client_id"] != expected_client_id:
        errors.append(f"client_id must be {expected_client_id!r}")
    scope = claim.get("scope")
    if not isinstance(scope, dict) or scope.get("type") not in SCOPE_TYPES:
        errors.append("scope.type must be client, opportunity, or project")
    elif scope["type"] != "client" and not scope.get("id"):
        errors.append("scope.id is required for opportunity and project claims")
    if claim.get("claim_type") not in CLAIM_TYPES:
        errors.append(f"unsupported claim_type: {claim.get('claim_type')!r}")
    if claim.get("status") not in CLAIM_STATUSES:
        errors.append(f"unsupported status: {claim.get('status')!r}")
    if not isinstance(claim.get("confidence"), (int, float)) or not 0 <= claim["confidence"] <= 1:
        errors.append("confidence must be between 0 and 1")
    if not isinstance(claim.get("source_refs"), list):
        errors.append("source_refs must be an array")
    if claim.get("sensitivity") not in SENSITIVITY_LEVELS:
        errors.append(f"unsupported sensitivity: {claim.get('sensitivity')!r}")
    if not isinstance(claim.get("predicate"), str) or "." not in claim["predicate"]:
        errors.append("predicate must be a dotted business path such as organization.main_business")
    return errors


def set_nested(target: dict[str, Any], dotted_path: str, value: Any) -> None:
    parts = dotted_path.split(".")
    cursor = target
    for part in parts[:-1]:
        node = cursor.get(part)
        if not isinstance(node, dict):
            node = {}
            cursor[part] = node
        cursor = node
    cursor[parts[-1]] = value


def claim_key(claim: dict[str, Any]) -> tuple[str, str, str, str]:
    scope = claim["scope"]
    return (scope["type"], scope.get("id", ""), claim["subject"], claim["predicate"])


def claim_rank(claim: dict[str, Any]) -> tuple[int, int, str, float]:
    type_rank = {
        "correction": 70,
        "verified_fact": 60,
        "customer_statement": 50,
        "supplier_evidence": 40,
        "internal_observation": 30,
        "inference": 20,
        "hypothesis": 10,
    }
    status_rank = {"confirmed": 40, "probable": 30, "unverified": 20, "stale": 10, "conflicted": 5}
    business_date = claim.get("effective_at") or claim.get("observed_at") or ""
    return (
        status_rank.get(claim.get("status"), 0),
        type_rank.get(claim.get("claim_type"), 0),
        business_date,
        float(claim.get("confidence", 0)),
    )


def find_ttl(predicate: str, policy: dict[str, Any]) -> int:
    rules = policy.get("rules", [])
    matches = [(len(rule.get("prefix", "")), int(rule["ttl_days"])) for rule in rules if predicate.startswith(rule.get("prefix", ""))]
    return max(matches, default=(0, int(policy.get("default_ttl_days", 180))))[1]
