#!/usr/bin/env python3
"""Render a self-contained client overview and evidence audit from canonical JSON."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

from client_profile_lib import client_dir, iter_claim_paths, load_json, now_iso, read_jsonl


def flatten_packets(node: object, path: str = "") -> list[tuple[str, dict]]:
    rows = []
    if isinstance(node, dict):
        if "claim_refs" in node and "value" in node:
            rows.append((path, node))
        else:
            for key, value in node.items():
                rows.extend(flatten_packets(value, f"{path}.{key}" if path else key))
    return rows


def display_value(value: object) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, indent=2)
    if value is None:
        return "未知"
    return str(value)


def card(path: str, packet: dict) -> str:
    status = html.escape(str(packet.get("status", "unknown")))
    freshness = html.escape(str(packet.get("freshness", "unknown")))
    return (
        '<article class="card">'
        f'<div class="eyebrow">{html.escape(path)}</div>'
        f'<div class="value">{html.escape(display_value(packet.get("value")))}</div>'
        f'<div class="meta"><span class="pill {status}">{status}</span>'
        f'<span class="pill {freshness}">{freshness}</span>'
        f'<span>置信度 {float(packet.get("confidence", 0)):.0%}</span>'
        f'<span>截至 {html.escape(str(packet.get("as_of", "未知")))}</span></div>'
        f'<details><summary>证据</summary><code>{html.escape(", ".join(packet.get("source_refs", [])) or "未登记来源")}</code></details>'
        '</article>'
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--client-id", required=True)
    args = parser.parse_args()
    skill_root = Path(__file__).resolve().parent.parent
    root = client_dir(args.workspace, args.client_id)
    client = load_json(root / "client.json")
    profile = load_json(root / "profile" / "current.json")
    rows = [(path, packet) for path, packet in flatten_packets(profile) if not path.startswith("profile_meta")]
    cards = "\n".join(card(path, packet) for path, packet in rows) or '<div class="empty">暂无已采纳画像信息</div>'
    opportunity_items = []
    for item in sorted((root / "opportunities").glob("*/opportunity.json")):
        data = load_json(item)
        opportunity_items.append(f'<li><strong>{html.escape(data["name"])}</strong><span>{html.escape(data["status"])}</span></li>')
    opportunities = "\n".join(opportunity_items) or "<li>暂无商机</li>"
    conflicts = load_json(root / "reviews" / "conflicts.json", {"conflicts": []})["conflicts"]
    conflict_html = "\n".join(f'<li>{html.escape(item["predicate"])} · {html.escape(", ".join(item["claim_refs"]))}</li>' for item in conflicts) or "<li>暂无冲突</li>"
    template = (skill_root / "assets" / "profile-view-template.html").read_text(encoding="utf-8")
    output = template.replace("{{CLIENT_NAME}}", html.escape(client["display_name"]))
    output = output.replace("{{CLIENT_ID}}", html.escape(client["client_id"]))
    output = output.replace("{{UPDATED_AT}}", html.escape(now_iso()))
    output = output.replace("{{FRESHNESS}}", html.escape(profile.get("profile_meta", {}).get("overall_freshness", "unknown")))
    output = output.replace("{{CARDS}}", cards).replace("{{OPPORTUNITIES}}", opportunities).replace("{{CONFLICTS}}", conflict_html)
    view_path = root / "views" / "client-overview.html"
    view_path.write_text(output, encoding="utf-8")

    claims = [claim for path in iter_claim_paths(root) for claim in read_jsonl(path)]
    audit_rows = "\n".join(
        "<tr>" + "".join(f"<td>{html.escape(display_value(value))}</td>" for value in (
            claim.get("claim_id"), claim.get("predicate"), claim.get("claim_type"), claim.get("status"),
            claim.get("observed_at"), ", ".join(claim.get("source_refs", [])),
        )) + "</tr>" for claim in claims
    )
    audit = template.replace("{{CLIENT_NAME}}", f"{html.escape(client['display_name'])} · 证据审计")
    audit = audit.replace("{{CLIENT_ID}}", html.escape(client["client_id"])).replace("{{UPDATED_AT}}", html.escape(now_iso())).replace("{{FRESHNESS}}", "audit")
    audit = audit.replace("{{CARDS}}", f'<div class="table-wrap"><table><thead><tr><th>Claim</th><th>字段</th><th>类型</th><th>状态</th><th>观察时间</th><th>来源</th></tr></thead><tbody>{audit_rows}</tbody></table></div>')
    audit = audit.replace("{{OPPORTUNITIES}}", "<li>证据审计视图</li>").replace("{{CONFLICTS}}", conflict_html)
    (root / "views" / "evidence-audit.html").write_text(audit, encoding="utf-8")
    print(json.dumps({"overview": str(view_path), "audit": str(root / 'views' / 'evidence-audit.html')}, ensure_ascii=False))


if __name__ == "__main__":
    main()
