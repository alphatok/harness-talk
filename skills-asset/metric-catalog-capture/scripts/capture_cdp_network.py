#!/usr/bin/env python3
"""Capture redacted BI request/response schemas from an authorized Chrome CDP target."""
from __future__ import annotations

import argparse, base64, hashlib, json, time, urllib.request
from pathlib import Path
from urllib.parse import urlsplit
from websockets.sync.client import connect


def canon(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value):
    return "sha256:" + hashlib.sha256(canon(value).encode()).hexdigest()


def shape(values, depth=0):
    if not values:
        return {"type": "unknown"}
    kinds = {"null" if v is None else "array" if isinstance(v, list) else "object" if isinstance(v, dict) else type(v).__name__ for v in values}
    if len(kinds) != 1:
        return {"anyOf": sorted(kinds)}
    kind = next(iter(kinds))
    if depth >= 7:
        return {"type": kind}
    if kind == "object":
        keys = sorted({k for v in values for k in v})
        return {
            "type": "object",
            "required": [k for k in keys if all(k in v for v in values)],
            "properties": {k: shape([v[k] for v in values if k in v], depth + 1) for k in keys},
        }
    if kind == "array":
        return {"type": "array", "items": shape([x for v in values for x in v[:3]], depth + 1), "observedLengths": sorted({len(v) for v in values})[:20]}
    return {"type": kind}


def parse_json(text):
    try:
        return json.loads(text)
    except Exception:
        return None


class CDP:
    def __init__(self, ws_url):
        self.ws = connect(ws_url, open_timeout=10, max_size=100 * 1024 * 1024)
        self.next_id = 1
        self.events = []
        self.reload_attached_iframes = False
        self.reloaded_sessions = set()

    def send(self, method, params=None, session_id=None):
        msg_id = self.next_id
        self.next_id += 1
        msg = {"id": msg_id, "method": method, "params": params or {}}
        if session_id:
            msg["sessionId"] = session_id
        self.ws.send(json.dumps(msg))
        while True:
            event = json.loads(self.ws.recv())
            if event.get("id") == msg_id:
                if event.get("error"):
                    raise RuntimeError(f"{method}: {event['error']}")
                return event.get("result", {})
            self.events.append(event)

    def collect(self, seconds):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            try:
                event = json.loads(self.ws.recv(timeout=max(0.1, deadline - time.monotonic())))
                self.events.append(event)
                if event.get("method") == "Target.attachedToTarget":
                    session_id = event.get("params", {}).get("sessionId")
                    if session_id:
                        try:
                            self.send("Network.enable", {"maxTotalBufferSize": 100_000_000, "maxResourceBufferSize": 50_000_000, "maxPostDataSize": 10_000_000}, session_id)
                            self.send("Runtime.enable", {}, session_id)
                            if self.reload_attached_iframes and event.get("params", {}).get("targetInfo", {}).get("type") == "iframe" and session_id not in self.reloaded_sessions:
                                self.reloaded_sessions.add(session_id)
                                self.send("Page.enable", {}, session_id)
                                self.send("Page.reload", {"ignoreCache": False}, session_id)
                        except Exception:
                            pass
            except TimeoutError:
                break


def runtime_bindings(post):
    out = {}
    if not isinstance(post, dict):
        return out
    for key in ("dashboardId", "releaseCode", "reportId", "widgetId", "widgetTitle", "widgetType", "requestId"):
        if key in post:
            out[key] = post[key]
    for parent, keys in (("param", ("datasetId", "metaId", "widgetId", "pageNum", "pageSize")), ("widgetInfo", ("id", "widgetId", "type", "title", "pid", "datasetId"))):
        value = post.get(parent)
        if isinstance(value, dict):
            for key in keys:
                if key in value and (value[key] is None or isinstance(value[key], (str, int, float, bool))):
                    out[f"{parent}.{key}"] = value[key]
    return out


def semantic_metadata(body):
    """Extract only whitelisted dashboard semantics from repo responses."""
    if not isinstance(body, dict) or not isinstance(body.get("data"), dict):
        return None
    data = body["data"]
    widgets = data.get("widgetRespVos")
    if not isinstance(widgets, list):
        return None
    help_keys = ("help", "tooltip", "explain", "description", "remark", "tips", "definition")
    title_keys = {"title", "name", "widgettitle"}

    def walk(value, found, depth=0):
        if depth > 8 or len(found["definitions"]) >= 80:
            return
        if isinstance(value, dict):
            for key, item in value.items():
                low = str(key).lower()
                if isinstance(item, str):
                    text = " ".join(item.split())
                    if 5 <= len(text) <= 4000 and any(token in low for token in help_keys):
                        found["definitions"].append({"field": str(key), "text": text})
                    elif 1 <= len(text) <= 200 and low in title_keys:
                        found["titles"].append(text)
                elif isinstance(item, (dict, list)):
                    walk(item, found, depth + 1)
        elif isinstance(value, list):
            for item in value[:200]:
                walk(item, found, depth + 1)

    output = []
    for widget in widgets[:300]:
        if not isinstance(widget, dict):
            continue
        found = {"titles": [], "definitions": []}
        for field in ("setting", "json", "jsonv2", "widgetFields"):
            raw = widget.get(field)
            parsed = parse_json(raw) if isinstance(raw, str) else raw
            if isinstance(parsed, (dict, list)):
                walk(parsed, found)
        titles = list(dict.fromkeys(found["titles"]))[:20]
        definitions = list({canon(item): item for item in found["definitions"]}.values())[:80]
        if titles or definitions:
            output.append({
                "widgetId": widget.get("widgetId") or widget.get("id"),
                "datasetId": widget.get("datasetId"),
                "titles": titles,
                "authoritativeDefinitionCandidates": definitions,
            })
    schema = data.get("schemaRespVo")
    dashboard_name = schema.get("name") if isinstance(schema, dict) and isinstance(schema.get("name"), str) else None
    config_found = {"titles": [], "definitions": []}
    if isinstance(schema, dict):
        raw_config = schema.get("config")
        parsed_config = parse_json(raw_config) if isinstance(raw_config, str) else raw_config
        if isinstance(parsed_config, (dict, list)):
            walk(parsed_config, config_found)
    return {
        "dashboardName": dashboard_name,
        "widgets": output,
        "configTitles": list(dict.fromkeys(config_found["titles"]))[:200],
        "configAuthoritativeDefinitionCandidates": list({canon(item): item for item in config_found["definitions"]}.values())[:200],
    }


def matched_request_ids(events, start, matches):
    ids = []
    for event in events[start:]:
        if event.get("method") != "Network.requestWillBeSent":
            continue
        params = event.get("params", {})
        url = params.get("request", {}).get("url", "")
        if any(token in url for token in matches):
            ids.append(params.get("requestId"))
    return list(dict.fromkeys(x for x in ids if x))


def action_expression(spec):
    """Build one generic, scoped, read-only DOM interaction."""
    payload = json.dumps(spec, ensure_ascii=False)
    return r"""(() => {
      const spec=%s, clean=s=>(s||'').replace(/\s+/g,' ').trim();
      const roots=[], seen=new Set(), elements=[];
      const visit=root=>{if(!root||seen.has(root))return;seen.add(root);roots.push(root);for(const el of (root.querySelectorAll?[...root.querySelectorAll('*')]:[])){elements.push(el);if(el.shadowRoot)visit(el.shadowRoot);if(el.tagName==='IFRAME'){try{if(el.contentDocument)visit(el.contentDocument)}catch(_){}}}};
      visit(document);
      const visible=el=>{try{const r=el.getBoundingClientRect(),s=getComputedStyle(el);return r.width>0&&r.height>0&&s.display!=='none'&&s.visibility!=='hidden'}catch(_){return false}};
      const within=el=>{if(!spec.withinText)return true;for(let p=el;p;p=p.parentElement){if(String(p.textContent||'').includes(spec.withinText))return true}return false};
      let candidates=elements;
      if(spec.text)candidates=candidates.filter(el=>clean(el.getAttribute('aria-label')||el.getAttribute('title')||el.textContent)===spec.text);
      if(spec.kind==='input')candidates=candidates.filter(el=>el.matches('input,textarea,[contenteditable=true]')||el.querySelector('input,textarea,[contenteditable=true]'));
      candidates=candidates.filter(el=>visible(el)&&within(el));
      candidates.sort((a,b)=>{const x=a.getBoundingClientRect(),y=b.getBoundingClientRect();return x.top-y.top||x.left-y.left||a.childElementCount-b.childElementCount});
      const occurrence=Math.max(1,Number(spec.occurrence||1)), chosen=candidates[occurrence-1];
      if(!chosen)return {matched:false,kind:spec.kind||'click',candidateCount:candidates.length};
      let target=chosen;
      if(spec.kind==='input')target=chosen.matches('input,textarea,[contenteditable=true]')?chosen:chosen.querySelector('input,textarea,[contenteditable=true]');
      else target=chosen.closest('button,[role=tab],[role=button],[role=combobox],label,[class*=tab],[class*=select],[class*=switch]')||chosen;
      if(spec.kind==='hover')for(const name of ['mouseover','mouseenter','mousemove'])target.dispatchEvent(new MouseEvent(name,{bubbles:true,view:window}));
      else if(spec.kind==='input'){
        const value=String(spec.value||''), proto=target.tagName==='TEXTAREA'?HTMLTextAreaElement.prototype:HTMLInputElement.prototype;
        const setter=Object.getOwnPropertyDescriptor(proto,'value')&&Object.getOwnPropertyDescriptor(proto,'value').set;
        if(setter)setter.call(target,value);else target.value=value;
        target.dispatchEvent(new Event('input',{bubbles:true}));target.dispatchEvent(new Event('change',{bubbles:true}));
      } else target.click();
      return {matched:true,kind:spec.kind||'click',tag:target.tagName,role:target.getAttribute&&target.getAttribute('role'),candidateCount:candidates.length};
    })()""" % payload


def interaction_state_expression():
    return r"""(() => {
      const clean=s=>(s||'').replace(/\s+/g,' ').trim(), seen=new Set(), elements=[];
      const visit=root=>{if(!root||seen.has(root))return;seen.add(root);for(const el of (root.querySelectorAll?[...root.querySelectorAll('*')]:[])){elements.push(el);if(el.shadowRoot)visit(el.shadowRoot);if(el.tagName==='IFRAME'){try{if(el.contentDocument)visit(el.contentDocument)}catch(_){}}}};visit(document);
      const visible=el=>{try{const r=el.getBoundingClientRect(),s=getComputedStyle(el);return r.width>0&&r.height>0&&s.display!=='none'&&s.visibility!=='hidden'}catch(_){return false}};
      const options=elements.filter(el=>el.matches&&el.matches('[role=option],.el-select-dropdown__item,.ant-select-item-option')&&visible(el));
      const tooltips=elements.filter(el=>el.matches&&el.matches('[role=tooltip],.el-tooltip__popper,.ant-tooltip-inner')&&visible(el)).map(el=>clean(el.innerText||el.textContent)).filter(Boolean);
      const emptyStateVisible=elements.some(el=>visible(el)&&['无数据','暂无数据','无选项'].includes(clean(el.innerText||el.textContent)));
      return {visibleOptionCount:options.length,visibleTooltipTexts:[...new Set(tooltips)].slice(0,20),emptyStateVisible};
    })()"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=9222)
    ap.add_argument("--page-url-contains", required=True)
    ap.add_argument("--navigate")
    ap.add_argument("--match", required=True, help="Verified read-only URL pattern for this platform")
    ap.add_argument("--extra-match", action="append", default=[], help="Additional known read-only URL substring; repeatable")
    ap.add_argument("--settle-seconds", type=float, default=10)
    ap.add_argument("--no-reload", action="store_true", help="Attach to the current page state without reload; useful for bounded manual capture")
    ap.add_argument("--click-text", action="append", default=[], help="Exact safe tab/view label to click after load; repeatable")
    ap.add_argument("--after-click-seconds", type=float, default=4)
    ap.add_argument("--scroll-passes", type=int, default=0, help="Bounded lazy-load scroll passes after initial load")
    ap.add_argument("--after-scroll-seconds", type=float, default=2)
    ap.add_argument("--reload-attached-iframes", action="store_true", help="Reload attached iframe after its Network domain is enabled")
    ap.add_argument("--click-first-option", action="store_true", help="After safe label clicks, select the first visible non-disabled option without persisting its value")
    ap.add_argument("--action", action="append", default=[], help="JSON goal action: click/open/hover/input with optional text, withinText, occurrence, value")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    if args.navigate and args.no_reload:
        ap.error("--navigate and --no-reload cannot be used together")
    matches = [args.match, *args.extra_match]
    action_specs = []
    for raw in args.action:
        try:
            spec = json.loads(raw)
        except json.JSONDecodeError as exc:
            ap.error(f"invalid --action JSON: {exc}")
        if not isinstance(spec, dict) or spec.get("kind", "click") not in {"click", "open", "hover", "input"}:
            ap.error("--action must be an object with kind click/open/hover/input")
        action_specs.append(spec)

    targets = json.load(urllib.request.urlopen(f"http://127.0.0.1:{args.port}/json/list"))
    pages = [x for x in targets if x.get("type") == "page" and args.page_url_contains in x.get("url", "")]
    if not pages:
        raise SystemExit("target page not found")
    target = pages[0]
    cdp = CDP(target["webSocketDebuggerUrl"])
    cdp.reload_attached_iframes = args.reload_attached_iframes
    cdp.send("Page.enable")
    cdp.send("Network.enable", {"maxTotalBufferSize": 100_000_000, "maxResourceBufferSize": 50_000_000, "maxPostDataSize": 10_000_000})
    cdp.send("Target.setAutoAttach", {"autoAttach": True, "waitForDebuggerOnStart": False, "flatten": True})
    for event in list(cdp.events):
        if event.get("method") == "Target.attachedToTarget" and event.get("params", {}).get("sessionId"):
            session_id = event["params"]["sessionId"]
            try:
                cdp.send("Network.enable", {"maxTotalBufferSize": 100_000_000, "maxResourceBufferSize": 50_000_000, "maxPostDataSize": 10_000_000}, session_id)
                cdp.send("Runtime.enable", {}, session_id)
                if args.reload_attached_iframes and event.get("params", {}).get("targetInfo", {}).get("type") == "iframe":
                    cdp.reloaded_sessions.add(session_id)
                    cdp.send("Page.enable", {}, session_id)
                    cdp.send("Page.reload", {"ignoreCache": False}, session_id)
            except Exception:
                pass
    cdp.events.clear()
    if args.navigate:
        cdp.send("Page.navigate", {"url": args.navigate})
    elif not args.no_reload:
        cdp.send("Page.reload", {"ignoreCache": False})
    cdp.collect(args.settle_seconds)
    scroll_results = []
    for pass_index in range(args.scroll_passes):
        sessions = [None] + sorted({event.get("params", {}).get("sessionId") for event in cdp.events if event.get("method") == "Target.attachedToTarget" and event.get("params", {}).get("sessionId")})
        touched = 0
        expression = """(() => {let n=0;const seen=new Set();const visit=(root,win)=>{if(!root||seen.has(root))return;seen.add(root);try{win&&win.scrollBy(0,Math.max(win.innerHeight,600))}catch(_){}for(const el of (root.querySelectorAll?[...root.querySelectorAll('*')]:[])){try{const s=(win||window).getComputedStyle(el);if((s.overflowY==='auto'||s.overflowY==='scroll')&&el.scrollHeight>el.clientHeight+20){el.scrollTop=Math.min(el.scrollHeight,el.scrollTop+Math.max(el.clientHeight,400));n++}}catch(_){}if(el.shadowRoot)visit(el.shadowRoot,win);if(el.tagName==='IFRAME'){try{if(el.contentDocument)visit(el.contentDocument,el.contentWindow)}catch(_){}}}};visit(document,window);return n;})()"""
        for session_id in sessions:
            try:
                value = cdp.send("Runtime.evaluate", {"expression": expression, "returnByValue": True}, session_id).get("result", {}).get("value", 0)
                touched += int(value or 0)
            except Exception:
                continue
        scroll_results.append({"pass": pass_index + 1, "scrollContainersTouched": touched})
        cdp.collect(args.after_scroll_seconds)
    click_results = []
    for label in args.click_text:
        action_start = len(cdp.events)
        encoded = json.dumps(label, ensure_ascii=False)
        expression = """(() => {
          const wanted=%s, clean=s=>(s||'').replace(/\\s+/g,' ').trim(), seen=new Set(), matches=[];
          const visit=root=>{if(!root||seen.has(root))return;seen.add(root);for(const el of (root.querySelectorAll?[...root.querySelectorAll('*')]:[])){if(clean(el.textContent)===wanted)matches.push(el);if(el.shadowRoot)visit(el.shadowRoot);if(el.tagName==='IFRAME'){try{if(el.contentDocument)visit(el.contentDocument)}catch(_){}}}};
          visit(document);if(!matches.length)return {clicked:false};const el=matches.sort((a,b)=>a.childElementCount-b.childElementCount)[0];const target=el.closest('button,[role=tab],[role=button],label,[class*=tab],[class*=switch]')||el;target.click();return {clicked:true,tag:target.tagName,role:target.getAttribute&&target.getAttribute('role')};
        })()""" % encoded
        sessions = [None] + sorted({event.get("params", {}).get("sessionId") for event in cdp.events if event.get("method") == "Target.attachedToTarget" and event.get("params", {}).get("sessionId")})
        value = {"clicked": False}
        for session_id in sessions:
            try:
                candidate = cdp.send("Runtime.evaluate", {"expression": expression, "returnByValue": True}, session_id).get("result", {}).get("value", {})
                if candidate.get("clicked"):
                    value = candidate
                    value["targetScope"] = "child" if session_id else "parent"
                    break
            except Exception:
                continue
        cdp.collect(args.after_click_seconds)
        click_results.append({"actionId": f"legacy-click-{len(click_results)+1}", "label": label, **value, "requestIds": matched_request_ids(cdp.events, action_start, matches)})
    action_results = []
    for index, spec in enumerate(action_specs, 1):
        action_start = len(cdp.events)
        sessions = [None] + sorted({event.get("params", {}).get("sessionId") for event in cdp.events if event.get("method") == "Target.attachedToTarget" and event.get("params", {}).get("sessionId")})
        value = {"matched": False, "kind": spec.get("kind", "click")}
        matched_session = None
        state_before = {}
        for session_id in sessions:
            try:
                before = cdp.send("Runtime.evaluate", {"expression": interaction_state_expression(), "returnByValue": True}, session_id).get("result", {}).get("value", {})
                candidate = cdp.send("Runtime.evaluate", {"expression": action_expression(spec), "returnByValue": True}, session_id).get("result", {}).get("value", {})
                if candidate.get("matched"):
                    value = {**candidate, "targetScope": "child" if session_id else "parent"}
                    matched_session = session_id
                    state_before = before
                    break
            except Exception:
                continue
        cdp.collect(args.after_click_seconds)
        if value.get("matched"):
            try:
                state = cdp.send("Runtime.evaluate", {"expression": interaction_state_expression(), "returnByValue": True}, matched_session).get("result", {}).get("value", {})
                before_tooltips = set(state_before.get("visibleTooltipTexts", []))
                state["visibleTooltipTexts"] = [text for text in state.get("visibleTooltipTexts", []) if text not in before_tooltips]
                value.update(state)
            except Exception:
                pass
        action_results.append({"actionId": f"action-{index}", "spec": {k: v for k, v in spec.items() if k != "value"}, **value, "requestIds": matched_request_ids(cdp.events, action_start, matches)})
    option_click_result = {"clicked": False}
    if args.click_first_option:
        sessions = [None] + sorted({event.get("params", {}).get("sessionId") for event in cdp.events if event.get("method") == "Target.attachedToTarget" and event.get("params", {}).get("sessionId")})
        expression = """(() => {const selectors='[role=option]:not([aria-disabled=true]),.el-select-dropdown__item:not(.is-disabled),.ant-select-item-option:not(.ant-select-item-option-disabled)';const options=[...document.querySelectorAll(selectors)].filter(el=>{const r=el.getBoundingClientRect();const s=getComputedStyle(el);return r.width>0&&r.height>0&&s.visibility!=='hidden'&&s.display!=='none'});if(!options.length)return {clicked:false};options[0].click();return {clicked:true,tag:options[0].tagName,role:options[0].getAttribute('role')};})()"""
        for session_id in sessions:
            try:
                candidate = cdp.send("Runtime.evaluate", {"expression": expression, "returnByValue": True}, session_id).get("result", {}).get("value", {})
                if candidate.get("clicked"):
                    option_click_result = {**candidate, "targetScope": "child" if session_id else "parent"}
                    break
            except Exception:
                continue
        cdp.collect(args.after_click_seconds)

    requests, responses, finished = {}, {}, set()
    for event in cdp.events:
        method, params = event.get("method"), event.get("params", {})
        if method == "Network.requestWillBeSent" and any(token in params.get("request", {}).get("url", "") for token in matches):
            requests[params["requestId"]] = {"request": params["request"], "sessionId": event.get("sessionId")}
        elif method == "Network.responseReceived" and params.get("requestId") in requests:
            responses[params["requestId"]] = params.get("response", {})
        elif method == "Network.loadingFinished" and params.get("requestId") in requests:
            finished.add(params["requestId"])

    observations = []
    for request_id, meta in requests.items():
        req, session_id = meta["request"], meta.get("sessionId")
        post_text = req.get("postData", "")
        if not post_text and req.get("hasPostData"):
            try:
                post_text = cdp.send("Network.getRequestPostData", {"requestId": request_id}, session_id).get("postData", "")
            except Exception:
                pass
        post, body, body_error = parse_json(post_text), None, None
        if request_id in finished:
            try:
                result = cdp.send("Network.getResponseBody", {"requestId": request_id}, session_id)
                text = result.get("body", "")
                if result.get("base64Encoded"):
                    text = base64.b64decode(text).decode("utf-8", "replace")
                body = parse_json(text)
            except Exception as exc:
                body_error = str(exc)
        response = responses.get(request_id, {})
        request_shape = shape([post]) if post is not None else {"type": "unparsed", "length": len(post_text)}
        response_shape = shape([body]) if body is not None else None
        code = body.get("errcode", body.get("code", body.get("errCode"))) if isinstance(body, dict) else None
        parts = urlsplit(req.get("url", ""))
        observations.append({
            "requestId": request_id, "method": req.get("method"), "path": parts.path + (("?" + parts.query) if parts.query else ""),
            "requestSchema": request_shape, "requestSchemaHash": digest(request_shape), "runtimeBindings": runtime_bindings(post),
            "httpStatus": response.get("status"), "mimeType": response.get("mimeType"), "businessCode": code,
            "responseSchema": response_shape, "responseSchemaHash": digest(response_shape) if response_shape else None, "responseBodyError": body_error,
            "responseSemanticMetadata": semantic_metadata(body),
        })
    page = {"targetId": target["id"], "url": target["url"], "title": target.get("title")}
    try:
        current = cdp.send("Runtime.evaluate", {"expression": "({url:location.href,title:document.title})", "returnByValue": True}).get("result", {}).get("value", {})
        page.update({key: current[key] for key in ("url", "title") if current.get(key)})
    except Exception:
        pass
    output = {
        "schemaVersion": "1.0", "kind": "redacted-cdp-network-capture", "capturedAt": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "page": page, "match": args.match, "matches": matches,
        "requestCount": len(observations), "observations": observations,
        "safeClickResults": click_results,
        "actionResults": action_results,
        "safeOptionClickResult": option_click_result,
        "safeScrollResults": scroll_results,
        "redaction": {"headersPersisted": False, "credentialsPersisted": False, "rawResponseBodiesPersisted": False, "rawBusinessRowsPersisted": False},
    }
    Path(args.out).write_text(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"out": args.out, "requests": len(observations), "statuses": sorted({x["httpStatus"] for x in observations if x["httpStatus"] is not None})}, ensure_ascii=False))


if __name__ == "__main__":
    main()
