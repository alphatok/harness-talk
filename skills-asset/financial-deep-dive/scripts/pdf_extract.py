#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Minimal PDF text extractor for HKEX filings — standard library only.

- 遍历页面树，按页顺序输出文本
- 处理 FlateDecode 内容流、Tj/TJ 字面量字符串与十六进制字符串
- 字面量解码：UTF-16BE(BOM) > UTF-8(尝试) > GBK(尝试) > latin-1
- CID 字体：解析 ToUnicode bfchar 映射（HKEX 文件常见形态）
- 用法: python3 pdf_extract.py 文件.pdf [-o 输出.txt]
"""
import re
import zlib
import argparse


def decompress(raw: bytes) -> bytes:
    raw = raw.strip(b"\r\n")
    try:
        return zlib.decompress(raw)
    except Exception:
        try:
            return zlib.decompress(raw, -15)
        except Exception:
            return b""


def obj_table(data: bytes):
    objs = {}
    for m in re.finditer(rb"(\d+)\s+(\d+)\s+obj", data):
        end = data.find(b"endobj", m.end())
        if end == -1:
            continue
        objs[int(m.group(1))] = data[m.end():end]
    expand_objstm(objs)
    return objs


def expand_objstm(objs: dict):
    """PDF 1.5+：对象存放于压缩对象流（/Type/ObjStm）内部，明文无 'N g obj' 头。
    展开：流头为 2N 个整数（对象号+字节偏移），对象体随附其后、从 /First 起算。
    （HKEX 部分 PDF-1.6 文件页面树整体在 ObjStm 内，导致 pages=0、提取 0 字符）"""
    for onum, body in list(objs.items()):
        if not re.search(rb"/Type\s*/ObjStm\b", body):
            continue
        s = stream_of(body)
        mN = re.search(rb"/N\s+(\d+)", body)
        mF = re.search(rb"/First\s+(\d+)", body)
        if not s or not mN or not mF:
            continue
        n, first = int(mN.group(1)), int(mF.group(1))
        if n <= 0 or n > 100000:
            continue
        pos, nums = 0, []
        while len(nums) < 2 * n:
            mm = re.match(rb"\s*(\d+)", s[pos:])
            if not mm:
                break
            nums.append(int(mm.group(1)))
            pos += mm.end()
        if len(nums) < 2 * n:
            continue
        for i in range(n):
            off = first + nums[2 * i + 1]
            end = first + nums[2 * i + 3] if 2 * i + 3 < 2 * n else len(s)
            objs[nums[2 * i]] = s[off:end]


def stream_of(obj_body: bytes) -> bytes:
    m = re.search(rb"stream\r?\n(.*?)endstream", obj_body, re.S)
    return decompress(m.group(1)) if m else b""


def decode_literal(b: bytes) -> str:
    if not b:
        return ""
    if b.startswith(b"\xfe\xff"):
        try:
            return b[2:].decode("utf-16-be")
        except Exception:
            pass
    if all(c < 128 for c in b):
        return b.decode("latin-1")
    for enc in ("utf-8", "gbk"):
        try:
            return b.decode(enc)
        except Exception:
            continue
    return b.decode("latin-1")


def parse_tounicode(stream: bytes):
    """返回 {cid_int: str}，支持 bfchar 与单目标 bfrange。"""
    cmap = {}
    text = stream.decode("latin-1", "ignore")
    for m in re.finditer(r"<([0-9a-fA-F]+)>\s*<([0-9a-fA-F]+)>", text):
        cid = int(m.group(1), 16)
        uni = bytes.fromhex(m.group(2)).decode("utf-16-be", "ignore")
        cmap[cid] = uni
    for m in re.finditer(r"<([0-9a-fA-F]+)>\s*<([0-9a-fA-F]+)>\s*<([0-9a-fA-F]+)>", text):
        try:
            lo, hi = int(m.group(1), 16), int(m.group(2), 16)
            dst = bytes.fromhex(m.group(3)).decode("utf-16-be", "ignore")
            for i, cid in enumerate(range(lo, hi + 1)):
                cmap[cid] = dst[i]
        except Exception:
            continue
    return cmap


def font_map_of(page_body: bytes, objs):
    """/Resources <</Font <</T1_0 12 0 R ...>>>> → {name: {cid->unicode}}"""
    result = {}
    m = re.search(rb"/Resources\s*<<(.*?)>>", page_body, re.S)
    if not m:
        return result
    res = m.group(1)
    if b"/Font" not in res:
        return result
    fm = re.search(rb"/Font\s*<<(.*?)>>", res, re.S)
    if not fm:
        return result
    for rec in re.finditer(rb"/([\w.\-]+)\s+(\d+)\s+(\d+)\s+R", fm.group(1)):
        name = rec.group(1).decode()
        onum = int(rec.group(2))
        if onum not in objs:
            continue
        tobj = objs[onum]
        tm = re.search(rb"/ToUnicode\s+(\d+)\s+(\d+)\s+R", tobj)
        if not tm:
            continue
        tsrc = int(tm.group(1))
        if tsrc in objs:
            result[name] = parse_tounicode(stream_of(objs[tsrc]))
    return result


def extract_pages(data: bytes):
    objs = obj_table(data)
    pages = []
    kids_seen = set()

    def parse_kids(body: bytes):
        out = []
        idx = body.find(b"/Kids")
        if idx == -1:
            return out
        for m in re.finditer(rb"[\[\s,](\d+)\s+(\d+)\s+R", body[idx:]):
            num, gen = int(m.group(1)), int(m.group(2))
            key = (num, gen)
            if key in kids_seen:
                continue
            kids_seen.add(key)
            if num in objs:
                out.append(objs[num])
        return out

    root = None
    for body in objs.values():
        if re.search(rb"/Type\s*/Pages\b", body):
            root = body
            break
    if root is not None:
        stack = [root]
        while stack:
            body = stack.pop()
            if re.search(rb"/Type\s*/Page\b", body):
                pages.append(body)
            for child in parse_kids(body):
                stack.append(child)
    if not pages:
        for body in objs.values():
            if re.search(rb"/Type\s*/Page\b", body):
                pages.append(body)
    return pages, objs


def extract_text(data: bytes) -> str:
    pages, objs = extract_pages(data)
    out = []
    for i, page in enumerate(pages, 1):
        texts = []
        fmap = font_map_of(page, objs)
        cur_font = None
        content = []
        for m in re.finditer(rb"/Contents\s+(\d+)\s+(\d+)\s+R", page):
            onum = int(m.group(1))
            if onum in objs:
                content.append(stream_of(objs[onum]))
        if not content:
            m = re.search(rb"/Contents\s+(<{0,1}[^>/]*>{0,1})", page)
            if m:
                body = m.group(1)
                if re.fullmatch(rb"[\s\dR]+", body):
                    for mm in re.finditer(rb"(\d+)\s+(\d+)\s+R", body):
                        if int(mm.group(1)) in objs:
                            content.append(stream_of(objs[int(mm.group(1))]))
                else:
                    content.append(decompress(body))
        for c in content:
            if not c:
                continue
            for fm in re.finditer(rb"/([\w.\-]+)\s+[\d.]+\s+Tf", c):
                cur_font = fm.group(1).decode()
            for m in re.finditer(rb"\[((?:\((?:[^()\\]|\\.)*\)[\d.\- ]*)+)\]\s*TJ|\((?:[^()\\]|\\.)*\)\s*Tj", c):
                lit = re.findall(rb"\(((?:[^()\\]|\\.)*)\)", m.group(0))
                txt = "".join(decode_literal(x) for x in lit)
                if txt:
                    texts.append(txt)
            for m in re.finditer(rb"<([0-9a-fA-F\s]{4,})>\s*Tj", c):
                hx = re.sub(rb"\s", b"", m.group(1))
                raw = bytes.fromhex(hx.decode())
                if raw.startswith(b"\xfe\xff"):
                    texts.append(raw[2:].decode("utf-16-be", "ignore"))
                elif cur_font and cur_font in fmap:
                    s = "".join(fmap[cur_font].get(int(hx[i:i+4], 16), "")
                                for i in range(0, len(hx) - 1, 4))
                    if s:
                        texts.append(s)
        page_text = " ".join(texts).replace("\x00", "")
        if page_text.strip():
            out.append(f"\n========== PAGE {i} ==========\n" + page_text)
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("-o", "--out")
    args = ap.parse_args()
    data = open(args.pdf, "rb").read()
    text = extract_text(data)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"OK {args.out} ({len(text)} chars)")
    else:
        print(text)


if __name__ == "__main__":
    main()