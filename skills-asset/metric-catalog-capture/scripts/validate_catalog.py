#!/usr/bin/env python3
"""Validate coverage, contract refs, execution checks, and privacy."""
import argparse,json,pathlib,re,sys
from capture_catalog import KINDS,CHECKS,STATES,nodes,secrets
def check(cat,con,md):
 errors=[]; blockers=[]; ops={c.get("operationId"):c for c in con.get("contracts",[]) if c.get("operationId")}; dc=cc=ec=0;seen=set()
 for d in cat.get("dashboards",[]):
  dc+=1;k=d.get("key")
  if not k or k in seen:errors.append(f"missing/duplicate dashboard: {k}")
  seen.add(k)
  if d.get("captureStatus") not in STATES:errors.append(f"{k}: invalid captureStatus")
  if d.get("captureStatus") in {"blocked","ignored_with_reason"} and not d.get("statusReason"):errors.append(f"{k}: statusReason required")
  if d.get("captureStatus")=="blocked":blockers.append({"key":str(k),"reason":d.get("statusReason","blocked")})
  for field,x in nodes(d):
   cc+=1; q=f"{k}/{x.get('key')}"
   if x.get("captureStatus") not in STATES:errors.append(q+": invalid captureStatus")
   if x.get("captureStatus") in {"blocked","ignored_with_reason"} and not x.get("statusReason"):errors.append(q+": statusReason required")
   if x.get("captureStatus")=="blocked":blockers.append({"key":q,"reason":x.get("statusReason","blocked")})
   if x.get("helpExpected") is True and x.get("definitionStatus") != "captured":blockers.append({"key":q,"reason":"authoritative help not captured"})
   if field not in {"widgets","controls"}:continue
   if x.get("kind") not in KINDS:errors.append(q+": invalid kind")
   refs=x.get("directOperationRefs",[])+x.get("dependencyOperationRefs",[])
   for op in refs:
    if op not in ops:errors.append(q+": missing operation "+op)
   if x.get("kind")=="data_leaf":
    if not x.get("directOperationRefs"):blockers.append({"key":q,"reason":"data operation not discovered"})
    elif all(ops.get(op,{}).get("executionStatus")=="executable" for op in (x.get("verifiedOperationRefs") or x["directOperationRefs"])):ec+=1
    else:blockers.append({"key":q,"reason":"data operation not executable"})
   ref=f"catalog.json#dashboardKey={k}&widgetKey={x.get('key')}"
   if field=="widgets" and ref not in md:errors.append("missing index ref: "+ref)
 for op,c in ops.items():
  if c.get("executionStatus")=="executable" and not all(c.get("verification",{}).get(x) is True for x in CHECKS):errors.append(op+": invalid executable status")
 if dc==0:blockers.append({"key":"catalog","reason":"catalog is empty"})
 sp=secrets({"catalog":cat,"contracts":con});errors += ["secret-like key: "+x for x in sp]
 risky=bool(re.search(r"(?i)(authorization\s*:|cookie\s*:|bearer\s+[\w.-]{12,}|password\s*:)",md))
 if risky:errors.append("credential-like Markdown")
 return errors,{"schemaVersion":"1.0","status":"complete" if not errors and not blockers else "incomplete","counts":{"dashboards":dc,"components":cc,"executableDataLeaves":ec,"contracts":len(ops)},"errors":errors,"blockers":sorted(blockers,key=lambda x:(x["key"],x["reason"])),"privacy":{"secretLikeKeys":sp,"passed":not sp and not risky}}
def main(a):
 cat=json.loads(pathlib.Path(a.catalog).read_text(encoding="utf-8"));con=json.loads(pathlib.Path(a.contracts).read_text(encoding="utf-8"));md=pathlib.Path(a.index).read_text(encoding="utf-8");e,r=check(cat,con,md);p=pathlib.Path(a.coverage_out);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(r,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8");print(json.dumps(r["counts"],ensure_ascii=False));return bool(e)
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--catalog",required=True);p.add_argument("--contracts",required=True);p.add_argument("--index",required=True);p.add_argument("--coverage-out",required=True);raise SystemExit(main(p.parse_args()))
