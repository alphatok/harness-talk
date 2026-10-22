#!/usr/bin/env python3
"""Extract topic hierarchy and notes; does not execute document content."""
import argparse, json, zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

MAX_CONTENT_BYTES = 32 * 1024 * 1024

def json_topic(topic):
    if not isinstance(topic, dict) or not isinstance(topic.get('title', ''), str):
        raise ValueError('Invalid topic or title in content.json')
    children = topic.get("children", {})
    if not isinstance(children, dict):
        raise ValueError('Expected topic children groups in content.json')
    nodes = []
    if isinstance(children, dict):
        for group, items in children.items():
            if not isinstance(items, list):
                raise ValueError('Expected topic list in content.json')
            nodes.extend(dict(json_topic(item), group=group) for item in items)
    notes = topic.get("notes", {})
    return {"title": topic.get("title", ""), "notes": notes, "children": nodes,
            "reference": {k: topic[k] for k in ("href", "image") if k in topic}}

def local(tag):
    return tag.rsplit("}", 1)[-1]

def direct(node, name):
    return [child for child in node if local(child.tag) == name]

def xml_topic(topic):
    titles = direct(topic, "title")
    notes = direct(topic, "notes")
    nodes = []
    for container in direct(topic, "children"):
        for group in direct(container, "topics"):
            for child in direct(group, "topic"):
                nodes.append(dict(xml_topic(child), group=group.get("type", "attached")))
    return {"title": "".join(titles[0].itertext()) if titles else "",
            "notes": "\n".join("".join(n.itertext()) for n in notes),
            "children": nodes,
            "reference": {k: v for k, v in topic.attrib.items() if local(k) == "href"}}

def extract(path):
    path = Path(path)
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        name = "content.json" if "content.json" in names else "content.xml"
        if name not in names:
            raise ValueError("No supported content.json or content.xml")
        if archive.getinfo(name).file_size > MAX_CONTENT_BYTES:
            raise ValueError("Content exceeds extraction limit")
        raw = archive.read(name)
        if name.endswith("json"):
            data = json.loads(raw)
            if not isinstance(data, list):
                raise ValueError("Expected a sheet list in content.json")
            if any(not isinstance(s, dict) or 'rootTopic' not in s
                   or not isinstance(s.get('title', ''), str) for s in data):
                raise ValueError('Invalid sheet or missing rootTopic in content.json')
            sheets = [{"title": s.get("title", ""), "root": json_topic(s["rootTopic"])} for s in data]
        else:
            root = ET.fromstring(raw)
            sheets = []
            for sheet in direct(root, "sheet"):
                titles = direct(sheet, "title")
                for topic in direct(sheet, "topic"):
                    sheets.append({"title": titles[0].text if titles else "", "root": xml_topic(topic)})
        if not sheets:
            raise ValueError('No supported sheets found; extraction is incomplete')
        assets = [n for n in names if not n.endswith('/') and
                  (n.lower().startswith(('attachments/', 'resources/')) or
                   n.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.pdf', '.svg', '.webp')))
                  and not n.lower().startswith('thumbnails/')]
        return {"source_name": path.name, "sheets": sheets, "unextracted_assets": assets}

def render(data):
    output = ["# XMind 原文提取", "", "来源：" + data["source_name"], "",
              "> 仅提取主题、备注和引用；未执行任何测试。图片与附件仍需核对。", ""]
    def walk(node, depth):
        title = str(node["title"]).replace("\r\n", "\n").replace("\r", "\n")
        parts = title.split("\n")
        output.append("  " * depth + "- " + parts[0])
        output.extend("  " * (depth + 1) + part for part in parts[1:])
        notes = node.get("notes")
        if notes:
            text = notes if isinstance(notes, str) else json.dumps(notes, ensure_ascii=False)
            output.append("  " * (depth + 1) + "备注：" + text.replace("\n", " "))
        if node.get("reference"):
            output.append("  " * (depth + 1) + "引用：" + json.dumps(node["reference"], ensure_ascii=False))
        for child in node["children"]:
            walk(child, depth + 1)
    for sheet in data["sheets"]:
        output.extend(["## " + (sheet["title"] or "未命名画布"), ""])
        walk(sheet["root"], 0)
        output.append("")
    return "\n".join(output) + "\n"

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    try:
        data = extract(args.input)
    except (OSError, ValueError, zipfile.BadZipFile, ET.ParseError, RecursionError):
        parser.error('无法完整提取：文件不可读、格式损坏、结构不支持或超出限制。原文件未改动。')
    args.out.mkdir(parents=True, exist_ok=True)
    targets = [args.out / "原文提取.md", args.out / "原文主题树.json"]
    if any(t.exists() for t in targets):
        parser.error("Output exists; choose a new output directory to preserve prior files")
    targets[0].write_text(render(data), encoding="utf-8")
    targets[1].write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"sheets": len(data["sheets"]), "assets_to_review": len(data["unextracted_assets"]),
                      "outputs": [str(t.resolve()) for t in targets]}, ensure_ascii=False))
if __name__ == "__main__":
    main()
