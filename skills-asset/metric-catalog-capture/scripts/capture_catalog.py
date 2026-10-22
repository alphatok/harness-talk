#!/usr/bin/env python3
"""Initialize/validate redacted browser-exported metric CaptureRuns."""
import argparse, datetime as dt, json, pathlib, re, sys, uuid

STATES={"captured","ignored_with_reason","blocked"}; KINDS={"data_leaf","composite","filter","layout","navigation"}
SECRET=re.compile(r"authorization|cookie|password|passwd|access[_-]?token|refresh[_-]?token|session[_-]?(id|ticket)|secret",re.I)
CHECKS=("http200","businessSuccess","responseSchemaMatched","targetFieldsProjected")

def write(path,obj):
 p=pathlib.Path(path).expanduser(); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
def secrets(x,p=""):
 out=[]
 if isinstance(x,dict):
  for k,v in x.items():
   q=f"{p}/{k}"; out += ([q] if SECRET.search(str(k)) else []) + secrets(v,q)
 elif isinstance(x,list):
  for i,v in enumerate(x): out += secrets(v,f"{p}/{i}")
 return out
def nodes(x):
 for field in ("tabs","subTabs","panels","controls","widgets","children"):
  for child in x.get(field,[]): yield field,child; yield from nodes(child)
def validate(run):
 e=[]; req={"schemaVersion","kind","captureId","observedAt","entryUrl","scope","idMode","browser","scopeKey","status"}
 if req-run.keys(): e.append("missing fields: "+", ".join(sorted(req-run.keys())))
 if run.get("kind")!="metric-catalog-capture-run": e.append("invalid kind")
 if run.get("scope") not in {"url","menu"}: e.append("invalid scope")
 if run.get("idMode") not in {"reuse","progressive"}: e.append("invalid idMode")
 seen=set()
 for d in run.get("dashboards",[]):
  key=d.get("key");
  if not key or key in seen: e.append(f"missing/duplicate dashboard key: {key}")
  seen.add(key)
  for field,n in [("dashboard",d),*nodes(d)]:
   ident=n.get("key",key); state=n.get("captureStatus")
   if state not in STATES:e.append(f"{key}/{ident}: invalid captureStatus")
   if state in {"blocked","ignored_with_reason"} and not n.get("statusReason"):e.append(f"{key}/{ident}: statusReason required")
   if field in {"controls","widgets"} and n.get("kind") not in KINDS:e.append(f"{key}/{ident}: invalid kind")
 ops=set()
 for c in run.get("contracts",[]):
  op=c.get("operationId")
  if not op or op in ops:e.append(f"missing/duplicate operationId: {op}")
  ops.add(op)
  if c.get("method") not in {"GET","POST"}:e.append(f"{op}: invalid method")
  if not str(c.get("path","")).startswith("/"):e.append(f"{op}: path must be relative")
  if c.get("executionStatus")=="executable" and not all(c.get("verification",{}).get(k) is True for k in CHECKS):e.append(f"{op}: executable without four checks")
 red=run.get("redaction",{})
 if red.get("credentialsPersisted") is not False or red.get("rawBusinessRowsPersisted") is not False:e.append("redaction assertions must be false")
 e += ["secret-like key: "+p for p in secrets(run)]; return e
def init(a):
 now=a.observed_at or dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
 obj={"schemaVersion":"1.0","kind":"metric-catalog-capture-run","captureId":a.capture_id or now.replace(":","")+"-"+uuid.uuid4().hex[:8],"observedAt":now,"entryUrl":a.entry_url,"scope":a.scope,"idMode":a.id_mode,"browser":a.browser,"scopeKey":a.scope_key,"status":"in_progress","dashboards":[],"contracts":[],"instanceBindings":[],"actions":[],"blockers":[],"redaction":{"credentialsPersisted":False,"rawBusinessRowsPersisted":False}}
 write(a.out,obj); print(a.out); return 0
def check(a):
 obj=json.loads(pathlib.Path(a.capture_run).expanduser().read_text(encoding="utf-8")); e=validate(obj)
 for x in e: print("ERROR: "+x,file=sys.stderr)
 if not e: print("valid capture run: "+obj["captureId"])
 return bool(e)
def cli():
 p=argparse.ArgumentParser(); s=p.add_subparsers(required=True)
 i=s.add_parser("init"); i.add_argument("--entry-url",required=True); i.add_argument("--scope",choices=("url","menu"),default="url"); i.add_argument("--id-mode",choices=("reuse","progressive"),default="reuse"); i.add_argument("--browser",default="in_app"); i.add_argument("--scope-key",required=True); i.add_argument("--capture-id"); i.add_argument("--observed-at"); i.add_argument("--out",required=True); i.set_defaults(fn=init)
 v=s.add_parser("validate"); v.add_argument("capture_run"); v.set_defaults(fn=check)
 a=p.parse_args(); return a.fn(a)
if __name__=="__main__": raise SystemExit(cli())
