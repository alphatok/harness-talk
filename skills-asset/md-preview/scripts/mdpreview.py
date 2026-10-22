#!/usr/bin/env python3
"""md -> styled .preview.html (next to source) -> open in default browser."""
import sys, os, re, argparse, html, webbrowser
from html.parser import HTMLParser
from urllib.parse import urlsplit

CSS = """
html{scroll-behavior:smooth;-webkit-text-size-adjust:100%}
:root{
  --bg:#ffffff;--fg:#1c2028;--fg-soft:#4a5261;--muted:#7b8494;
  --border:#e4e8ec;--border-strong:#d3dae2;
  --accent:#2c6e49;--accent-soft:#eef4f0;
  --toc-bg:#f7f9f8;--quote-bg:#f5f7f6;
  --code-bg:#f2f4f6;--pre-bg:#f6f8fa;
  --link:#17628f;--th-bg:#eef4f0;--stripe:#fafbfc;
  --shadow:0 1px 2px rgba(23,32,43,.06);
}
@media (prefers-color-scheme:dark){
  :root{
    --bg:#14171c;--fg:#e7eaf0;--fg-soft:#c6cdd8;--muted:#8d96a5;
    --border:#2a313b;--border-strong:#3a434f;
    --accent:#8ed3a8;--accent-soft:#1f2a24;
    --toc-bg:#1a1e25;--quote-bg:#1c2128;
    --code-bg:#232933;--pre-bg:#1d2229;
    --link:#8cc3ea;--th-bg:#212d26;--stripe:#191d23;
    --shadow:0 1px 2px rgba(0,0,0,.45);
  }
}
body{
  margin:0;
  font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB","Microsoft YaHei","Helvetica Neue",sans-serif;
  font-size:16.5px;line-height:1.8;color:var(--fg);background:var(--bg);
  -webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale;
  text-rendering:optimizeLegibility;
  overflow-wrap:break-word;
}
.layout{max-width:1180px;margin:0 auto;padding:28px 24px 80px;display:flex;gap:28px;align-items:flex-start}
aside#toc{position:sticky;top:20px;flex:0 0 296px;max-height:calc(100vh - 40px);overflow:auto;background:var(--toc-bg);border:1px solid var(--border);border-radius:12px;padding:14px 6px 16px 4px;font-size:13px;line-height:1.75;color:var(--fg-soft);scrollbar-width:thin;box-shadow:var(--shadow)}
.toc-title{font-weight:650;color:var(--accent);font-size:14px;padding:2px 14px 10px;border-bottom:1px solid var(--border);margin-bottom:8px;letter-spacing:.04em}
aside#toc ul{list-style:none;margin:0;padding:0}
aside#toc ul ul{padding-left:14px}
aside#toc a{display:block;color:var(--fg-soft);text-decoration:none;padding:4px 12px;border-left:2px solid transparent;transition:background .12s,color .12s,border-color .12s}
aside#toc a:hover{color:var(--accent);background:var(--accent-soft);border-left-color:var(--accent)}
main{flex:1;min-width:0}
h1,h2,h3,h4{scroll-margin-top:16px;font-weight:650;line-height:1.4;color:var(--fg)}
h1{font-size:28px;border-bottom:2px solid var(--accent);padding-bottom:12px;margin:6px 0 28px}
h2{font-size:21px;margin-top:44px;color:var(--accent)}
h3{font-size:17px;margin-top:30px}
h4{font-size:16px;margin-top:24px}
strong{font-weight:650}
main img{max-width:100%;height:auto}
.table-wrap{overflow-x:auto;-webkit-overflow-scrolling:touch;margin:16px 0;border:1px solid var(--border);border-radius:10px;box-shadow:var(--shadow)}
table{border-collapse:collapse;min-width:100%;width:auto;margin:0}
th,td{border:1px solid var(--border);padding:8px 12px;text-align:left;vertical-align:top;font-size:14px;overflow-wrap:break-word;word-break:normal}
th{background:var(--th-bg);font-weight:650;color:var(--fg)}
tr:nth-child(even) td{background:var(--stripe)}
table img{width:46px;height:46px;object-fit:contain;border-radius:4px}
table p{margin:0}
/* 窄屏：侧栏下沉、正文全宽、仅表头不换行避免被压缩 */
@media (max-width: 900px){
  .layout{flex-direction:column;gap:14px;padding:18px 12px 64px}
  aside#toc{position:static;flex:none;max-height:none;width:auto;margin-bottom:6px}
  main{width:100%}
  h1{font-size:24px}
  pre{font-size:13px}
  table{font-size:13px}
  th,td{padding:6px 9px}
}
p:has(>img) img{max-width:min(640px,100%);border:1px solid var(--border);border-radius:10px}
blockquote{border-left:4px solid var(--accent);background:var(--quote-bg);margin:14px 0;padding:10px 18px;color:var(--fg-soft);border-radius:0 8px 8px 0}
blockquote p{margin:6px 0}
code{background:var(--code-bg);padding:2px 6px;border-radius:5px;font-size:.87em;font-family:ui-monospace,"SF Mono",SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace}
pre{background:var(--pre-bg);border:1px solid var(--border);padding:16px;border-radius:10px;overflow-x:auto;font-size:13.5px;line-height:1.65;box-shadow:var(--shadow)}
pre code{background:none;padding:0;font-size:1em}
hr{border:none;border-top:1px solid var(--border);margin:32px 0}
a{color:var(--link);text-underline-offset:3px;text-decoration-thickness:1px}
::selection{background:rgba(44,110,73,.16)}
"""

# 图片放大全屏（仅在正文含图片时注入）
IMG_CSS = """
main img{cursor:zoom-in}
#lightbox{display:none;position:fixed;inset:0;z-index:9999;background:rgba(10,13,18,.9);backdrop-filter:blur(3px);align-items:center;justify-content:center;cursor:zoom-out}
#lightbox img{max-width:96vw;max-height:96vh;object-fit:contain;box-shadow:0 8px 40px rgba(0,0,0,.6)}
"""

JS = """<script nonce="mdpreview-local">
(function(){
  var lb=null;
  function open(img){
    if(!lb){lb=document.createElement('div');lb.id='lightbox';lb.innerHTML='<img alt="">';document.body.appendChild(lb);}
    lb.firstElementChild.src=img.currentSrc||img.src;
    lb.style.display='flex';
  }
  function close(){if(lb)lb.style.display='none';}
  document.addEventListener('click',function(e){
    var img=e.target.closest('main img');
    if(img){open(img);return;}
    if(lb&&lb.contains(e.target))close();
  });
  document.addEventListener('keydown',function(e){if(e.key==='Escape')close();});
})();
</script>
"""

class SafeHTML(HTMLParser):
    allowed = set("p br hr h1 h2 h3 h4 h5 h6 ul ol li blockquote pre code strong em del table thead tbody tr th td a img div span input dl dt dd".split())
    voids = {"br", "hr", "img", "input"}
    blocked = {"script", "style", "iframe", "object", "embed", "svg", "math", "form"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.output, self.depth = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in self.blocked:
            self.depth += 1
            return
        if self.depth or tag not in self.allowed:
            return
        clean = []
        for key, value in attrs:
            if value is None:
                continue
            if key in {"id", "class", "title", "alt", "colspan", "rowspan"}:
                clean.append((key, value))
            elif key in {"href", "src"}:
                scheme = urlsplit(value.strip()).scheme.lower()
                if not any(ord(c) < 32 for c in value) and scheme in {"", "http", "https"}:
                    clean.append((key, value))
        attributes = "".join(' ' + key + '="' + html.escape(value, quote=True) + '"' for key, value in clean)
        self.output.append('<' + tag + attributes + '>')

    def handle_endtag(self, tag):
        if tag in self.blocked:
            self.depth = max(0, self.depth - 1)
        elif not self.depth and tag in self.allowed and tag not in self.voids:
            self.output.append('</' + tag + '>')

    def handle_data(self, data):
        if not self.depth:
            self.output.append(html.escape(data))


def sanitize(fragment):
    parser = SafeHTML()
    parser.feed(fragment)
    return ''.join(parser.output)


def render(src, open_browser=True, overwrite=False):
    try:
        import markdown
    except ImportError as exc:
        raise RuntimeError("缺少Markdown库；请在选定的Python环境安装markdown后重试") from exc
    md = markdown.Markdown(
        extensions=["tables", "fenced_code", "sane_lists", "toc"],
        extension_configs={"toc": {"toc_depth": "2-3"}},
    )
    with open(src, encoding="utf-8") as stream:
        body = sanitize(md.convert(stream.read()))
    body = re.sub(r"(<table>.*?</table>)", r'<div class="table-wrap">\1</div>', body, flags=re.S)
    toc = sanitize(md.toc)
    toc_block = f'<aside id="toc"><div class="toc-title">目录</div>{toc}</aside>' if toc.strip() else ""
    title = html.escape(os.path.splitext(os.path.basename(src))[0])
    style = CSS + (IMG_CSS if "<img" in body else "")
    extra_css = os.path.splitext(src)[0] + ".preview.css"
    if os.path.exists(extra_css):
        with open(extra_css, encoding="utf-8") as stream:
            style += "\n" + stream.read().replace("</style", "<\\/style")
    js = JS if "<img" in body else ""
    csp = "default-src 'none'; img-src 'self' data: file:; style-src 'unsafe-inline'; script-src 'nonce-mdpreview-local'"
    page = f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="{csp}">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title><style>{style}</style></head><body>
<div class="layout">{toc_block}<main>{body}</main></div>{js}</body></html>'''
    out = os.path.splitext(src)[0] + ".preview.html"
    with open(out, "w" if overwrite else "x", encoding="utf-8") as stream:
        stream.write(page)
    if open_browser:
        webbrowser.open(__import__('pathlib').Path(out).as_uri())
    return out


def main():
    parser = argparse.ArgumentParser(description="把Markdown转为本地HTML阅读页")
    parser.add_argument("files", nargs="+")
    parser.add_argument("--no-open", action="store_true", help="只生成，不打开浏览器")
    parser.add_argument("--overwrite", action="store_true", help="替换已有preview.html；原Markdown不变")
    args = parser.parse_args()
    try:
        for value in args.files:
            src = os.path.abspath(value)
            result = render(src, open_browser=not args.no_open, overwrite=args.overwrite)
            print("预览已生成: " + result)
    except (OSError, RuntimeError) as exc:
        print("错误: " + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
