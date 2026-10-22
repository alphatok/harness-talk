#!/usr/bin/env python3
"""港股财报抓取与核验工具（仅标准库）—— hk-financials 技能配套脚本。

子命令：
  map <code>                                  股票代码 -> stockId / 公司名
  list <code> --from YYYYMMDD --to YYYYMMDD   列出文档清单（默认财务/ESG 类）
              [--cat financial|all] [--lang E|SC]
  download <file_link> -o <out.pdf>           下载 PDF（自动补全域名、带浏览器 UA）
  verify <pdf> [--name 关键词 ...]            四层核验：魔法字节/大小/页数/流内容指纹

示例：先运行 --help，再填入本次核对的股票代码、日期和官方PDF链接。

约定：
  - 双层 JSON：接口返回 {"result": "<JSON 字符串>"}，需两次 json.loads；
  - prefix.do 是 JSONP（callback(...) 包裹）；
  - 港交所要求浏览器 User-Agent；
  - verify 未通过时退出码非 0，便于在流水线里当断言用。
"""
import argparse
import json
import platform
import re
import subprocess
import sys
import urllib.parse
import urllib.request
import zlib
from pathlib import Path

BASE = "https://www1.hkexnews.hk"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15")

# 内容指纹的默认财务词（英中双语）；--name 追加公司名做实体级验证
DEFAULT_MARKERS = [
    b"CONSOLIDATED STATEMENT",
    b"STATEMENT OF COMPREHENSIVE INCOME",
    b"STATEMENT OF FINANCIAL POSITION",
    b"STATEMENT OF PROFIT OR LOSS",
    b"INCOME STATEMENT",
    b"CASH FLOW",
    "綜合損益".encode("utf-8"),
    "合併損益".encode("utf-8"),
    "損益表".encode("utf-8"),
    "收益".encode("utf-8"),
    "資產負債".encode("utf-8"),
]


def _get(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def map_code(code):
    code = str(code).strip()
    if not code.isdigit() or len(code) > 5:
        raise SystemExit("股票代码应为最多5位数字")
    url = BASE + "/search/prefix.do?" + urllib.parse.urlencode(
        {"callback": "cb", "lang": "EN", "type": "A", "name": code, "market": "SEHK"})
    body = _get(url)
    m = re.search(r"^[\w$.]+\((.*)\)\s*;?\s*$", body.strip(), re.S)
    if not m:
        raise SystemExit("prefix.do 返回非 JSONP，检查 UA/网络")
    data = json.loads(m.group(1))
    infos = data.get("stockInfo") or []
    if not infos:
        raise SystemExit(f"未找到代码 {code} 对应的港股（检查是否 4-5 位数字）")
    exact = [info for info in infos if str(info.get("code", "")).isdigit() and int(info["code"]) == int(code)]
    if len(exact) != 1:
        raise SystemExit("股票代码未唯一匹配，请在官方页面核对主体")
    return exact


def list_docs(code, from_date, to_date, cat="financial", lang="E", row_range=500):
    stock = map_code(code)[0]
    t1code = "-1" if cat == "all" else "40000"
    params = {
        "sortDir": "0", "sortByOptions": "DateTime", "category": "0",
        "market": "SEHK", "stockId": stock["stockId"], "documentType": "-1",
        "fromDate": from_date, "toDate": to_date, "title": "",
        "searchType": "1", "t1code": t1code, "t2Gcode": "-2",
        "t2code": "-1", "rowRange": str(row_range), "lang": lang,
    }
    url = BASE + "/search/titleSearchServlet.do?" + urllib.parse.urlencode(params)
    body = _get(url)
    try:
        rows = json.loads(json.loads(body)["result"])
    except Exception:
        raise SystemExit(f"清单接口解析失败（返回 {len(body)} 字节），请核对当前官方页面；未输出响应正文")
    return stock, rows


# ---------------- 子命令实现 ----------------

def cmd_map(args):
    for info in map_code(args.code):
        print(f"{info['code']} -> stockId={info['stockId']}  {info['name']}")


def cmd_list(args):
    stock, rows = list_docs(args.code, args.from_date, args.to_date,
                            cat=args.cat, lang=args.lang)
    print(f"# {stock['code']} {stock['name']}  {args.from_date}~{args.to_date}  共 {len(rows)} 条")
    for r in rows:
        link = r.get("FILE_LINK") or ""
        full = (BASE + link) if link.startswith("/") else link
        print("\t".join([r.get("DATE_TIME", ""), r.get("FILE_INFO", "").strip(),
                         r.get("TITLE", ""), full]))


def cmd_download(args):
    link = args.file_link
    full = link if link.startswith("http") else BASE + link
    parsed = urllib.parse.urlsplit(full)
    if parsed.scheme != "https" or not (parsed.hostname or "").endswith(".hkexnews.hk"):
        raise SystemExit("仅下载HTTPS披露易域名文件，请先核对官方来源")
    target = Path(args.out)
    if target.exists():
        raise SystemExit("目标文件已存在，未覆盖；请核对已有归档")
    req = urllib.request.Request(full, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        final = urllib.parse.urlsplit(r.geturl())
        if final.scheme != "https" or not (final.hostname or "").endswith(".hkexnews.hk"):
            raise SystemExit("下载重定向离开官方域名，未保存")
        data = r.read(128 * 1024 * 1024 + 1)
    if len(data) > 128 * 1024 * 1024 or not data.startswith(b"%PDF-"):
        raise SystemExit("内容不是PDF或超过128MiB，请在官方页面检查")
    with target.open("xb") as f:
        f.write(data)
    print(f"OK {args.out} <- {full}")


def _streams(data):
    for s in re.findall(rb"stream\r?\n(.*?)endstream", data, re.S):
        raw = s.strip(b"\r\n")
        try:
            yield zlib.decompress(raw)
        except Exception:
            continue


def _mdls_pages(path):
    try:
        out = subprocess.run(["mdls", "-name", "kMDItemNumberOfPages", "-raw", path],
                             capture_output=True, timeout=15, text=True)
        pages = out.stdout.strip()
        return int(pages) if pages.isdigit() else None
    except Exception:
        return None


def cmd_verify(args):
    data = open(args.pdf, "rb").read()
    res = {"file": args.pdf, "size": len(data),
           "magic_ok": data[:5] == b"%PDF-", "pages": None}
    if platform.system() == "Darwin":
        res["pages"] = _mdls_pages(args.pdf)

    needles = [bytes(n, "utf-8") for n in (args.name or [])]
    needles += DEFAULT_MARKERS
    hits = {n.decode("utf-8", "replace"): 0 for n in needles}
    scanned = 0
    for chunk in _streams(data):
        scanned += 1
        if scanned > 500:
            break
        low = chunk.lower()
        for n in needles:
            cnt = low.count(n.lower())
            if cnt:
                hits[n.decode("utf-8", "replace")] += cnt
    # 判定：魔法字节必须过；给定了公司名则公司名必须命中，否则任一财务词命中
    name_hits = sum(v for k, v in hits.items()
                    if k not in {m.decode("utf-8", "replace") for m in DEFAULT_MARKERS})
    marker_hits = sum(hits[m.decode("utf-8", "replace")] for m in DEFAULT_MARKERS)
    res["name_hits"] = name_hits
    res["marker_hits"] = marker_hits
    res["passed"] = bool(res["magic_ok"]) and (
        (name_hits > 0 if args.name else True) and marker_hits > 0)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    sys.exit(0 if res["passed"] else 1)


def main():
    p = argparse.ArgumentParser(prog="fetch_hkex.py", description="港交所披露易财报抓取与核验")
    sub = p.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("map", help="股票代码 -> stockId")
    sp.add_argument("code")
    sp.set_defaults(func=cmd_map)

    sp = sub.add_parser("list", help="列出文档清单")
    sp.add_argument("code")
    sp.add_argument("--from", dest="from_date", required=True, help="YYYYMMDD")
    sp.add_argument("--to", dest="to_date", required=True, help="YYYYMMDD")
    sp.add_argument("--cat", choices=["financial", "all"], default="financial")
    sp.add_argument("--lang", choices=["E", "SC"], default="E")
    sp.set_defaults(func=cmd_list)

    sp = sub.add_parser("download", help="下载 PDF")
    sp.add_argument("file_link")
    sp.add_argument("-o", "--out", required=True)
    sp.set_defaults(func=cmd_download)

    sp = sub.add_parser("verify", help="启发式初检，不替代实体/期间/完整性核验")
    sp.add_argument("pdf")
    sp.add_argument("--name", action="append", default=None,
                    help="追加实体名关键词（可多次），命中才算通过")
    sp.set_defaults(func=cmd_verify)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()