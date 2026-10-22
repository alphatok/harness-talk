#!/usr/bin/env python3
"""Deterministically merge validated CaptureRuns."""
import argparse, copy, json, pathlib, sys
from capture_catalog import validate, write, CHECKS
IDS={"dashboards":"key","widgets":"key","controls":"key","tabs":"key","subTabs":"key","panels":"key","children":"key","metrics":"key","contracts":"operationId"}
def canon(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def lists(a,b,field,conf,path):
 if field in IDS and all(isinstance(x,dict) for x in a+b):
  d={}
  for x in a+b:
   k=str(x.get(IDS[field],"")); d[k]=merge(d[k],x,conf,path+"/"+k) if k in d else copy.deepcopy(x)
  return [d[k] for k in sorted(d)]
 u={canon(x):copy.deepcopy(x) for x in a+b}; return [u[k] for k in sorted(u)]
def merge(a,b,conf,path=""):
 if a==b:return copy.deepcopy(a)
 if a is None:return copy.deepcopy(b)
 if b is None:return copy.deepcopy(a)
 if isinstance(a,dict) and isinstance(b,dict):
  r=copy.deepcopy(a)
  for k in sorted(b):
   if k not in r:r[k]=copy.deepcopy(b[k])
   elif k=="name" and isinstance(r[k],str) and isinstance(b[k],str) and r[k]!=b[k]:r["aliases"]=sorted(set(r.get("aliases",[])+[r[k]]));r[k]=b[k]
   elif k in {"observedAt","verifiedAt","discoveredAt"}:r[k]=max(str(r[k]),str(b[k]))
   else:r[k]=merge(r[k],b[k],conf,path+"/"+k)
  return r
 if isinstance(a,list) and isinstance(b,list):return lists(a,b,path.rsplit("/",1)[-1],conf,path)
 c={"path":path or "/","values":sorted([a,b],key=canon)}
 if canon(c) not in {canon(x) for x in conf}:conf.append(c)
 return copy.deepcopy(b)
def load(p,default):return json.loads(p.read_text(encoding="utf-8")) if p.exists() else copy.deepcopy(default)
def derive_execution(node,ops):
 kind=node.get("kind"); direct=node.get("directOperationRefs",[]); deps=node.get("dependencyOperationRefs",[])
 for field in ("widgets","children"):
  for child in node.get(field,[]):derive_execution(child,ops)
 verified=node.get("verifiedOperationRefs",[])
 refs=verified or (direct if kind in {"data_leaf","filter"} else deps if kind=="composite" else [])
 if refs:
  node["executionStatus"]="executable" if node.get("captureStatus")=="captured" and all(ops.get(x,{}).get("executionStatus")=="executable" for x in refs) else "needs_revalidation"
 elif kind in {"layout","navigation","filter"}:node["executionStatus"]="not_applicable"
 elif kind in {"data_leaf","composite"}:node["executionStatus"]="needs_revalidation"
def main(a):
 home=pathlib.Path(a.data_home).expanduser(); cp=home/"catalog/catalog.json"; xp=home/"catalog/contracts.json"
 cat=load(cp,{"schemaVersion":"1.0","kind":"metric-catalog","dashboards":[],"captureHistory":[],"conflicts":[]}); con=load(xp,{"schemaVersion":"1.0","kind":"metric-contracts","contracts":[],"captureHistory":[],"conflicts":[]})
 runs=[]
 for p in a.capture_runs:
  r=json.loads(pathlib.Path(p).read_text(encoding="utf-8")); e=validate(r)
  if e:
   print("; ".join(e),file=sys.stderr);return 1
  archive=home/"captures"/r["captureId"]/"capture-run.json"
  if archive.exists() and canon(json.loads(archive.read_text(encoding="utf-8")))!=canon(r):
   print(f"captureId already exists with different content: {r['captureId']}",file=sys.stderr);return 1
  if not archive.exists():write(archive,r)
  runs.append(r)
 for r in sorted(runs,key=lambda x:(x["observedAt"],x["captureId"])):
  cat["dashboards"]=lists(cat["dashboards"],r.get("dashboards",[]),"dashboards",cat["conflicts"],"/dashboards")
  before=len(con["conflicts"])
  con["contracts"]=lists(con["contracts"],r.get("contracts",[]),"contracts",con["conflicts"],"/contracts")
  conflicted={x.get("path","").split("/")[2] for x in con["conflicts"][before:] if x.get("path","").startswith("/contracts/")}
  for c in con["contracts"]:
   ok=all(c.get("verification",{}).get(k) is True for k in CHECKS)
   if c.get("operationId") in conflicted:c["executionStatus"]="needs_revalidation"
   elif ok:c["executionStatus"]="executable"
   elif c.get("executionStatus")=="executable":c["executionStatus"]="needs_revalidation"
  opmap={c.get("operationId"):c for c in con["contracts"] if c.get("operationId")}
  for d in cat["dashboards"]:
   for w in d.get("widgets",[]):derive_execution(w,opmap)
  cat["status"]="incomplete" if cat["dashboards"] else "empty"
  h={x["captureId"]:x for x in cat["captureHistory"]};h[r["captureId"]]={k:r[k] for k in ("captureId","observedAt","scopeKey","status")};cat["captureHistory"]=[h[k] for k in sorted(h)];con["captureHistory"]=cat["captureHistory"]
  if r.get("instanceBindings"):
   bp=home/"instances"/r["scopeKey"]/"bindings.json"; bd=load(bp,{"schemaVersion":"1.0","kind":"metric-instance-bindings","bindings":[]})
   key=lambda x:"|".join(str(x.get(k,"")) for k in ("scopeKey","dashboardTemplateKey","route","releaseFingerprint")); d={key(x):x for x in bd["bindings"]}
   for x in r["instanceBindings"]:d[key(x)]=merge(d[key(x)],x,bd.setdefault("conflicts",[]),"/bindings/"+key(x)) if key(x) in d else x
   bd["bindings"]=[d[k] for k in sorted(d)];write(bp,bd)
 write(cp,cat);write(xp,con);print(f"merged {len(runs)} run(s)");return 0
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--data-home",required=True);p.add_argument("capture_runs",nargs="+");raise SystemExit(main(p.parse_args()))
