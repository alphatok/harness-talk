#!/usr/bin/env python3
"""Render deterministic hierarchical Markdown from canonical JSON."""
import argparse,json,pathlib
def esc(x):return str(x).replace("\n","<br>").replace("|","\\|")
def option_text(x):
 if isinstance(x,dict):
  label=x.get("label",x.get("name",x.get("key",""))); value=x.get("value")
  return str(label) if value is None else f"{label} (`{value}`)"
 return str(x)
def tab_lines(items,depth=0):
 out=[]
 for x in sorted(items,key=lambda y:y.get("key","")):
  out.append("  "*depth+f"- {esc(x.get('name',x.get('label',x.get('key',''))))} — tabKey=`{esc(x.get('key',''))}`, status=`{esc(x.get('captureStatus','unknown'))}`")
  out+=tab_lines(x.get("subTabs",[]),depth+1)
 return out
def widget(w,dk,ops,depth=4):
 out=["#"*depth+" Widget: "+str(w.get("title") or w.get("name") or w["key"]),"",f"- widgetKey: `{w['key']}`",f"- kind: `{w.get('kind','unknown')}`",f"- captureStatus: `{w.get('captureStatus','unknown')}`",f"- definitionStatus: `{w.get('definitionStatus','unknown')}`",f"- executionStatus: `{w.get('executionStatus','unknown')}`"]
 if w.get("aliases"):out.append("- aliases: "+", ".join(esc(x) for x in w["aliases"]))
 if w.get("viewOptions"):out.append("- viewOptions: "+", ".join(option_text(x) for x in w["viewOptions"]))
 if w.get("returnFields"):out.append("- returnFields: "+", ".join(f"`{esc(x)}`" for x in w["returnFields"]))
 verified=set(w.get("verifiedOperationRefs",[])); historical=set(w.get("directOperationRefs",[])+w.get("dependencyOperationRefs",[]))-verified
 for op in sorted(verified):out.append(f"- verified operation: `{op}` (`{ops.get(op,{}).get('executionStatus','missing')}`)")
 for op in sorted(historical):out.append(f"- historical operation: `{op}` (`{ops.get(op,{}).get('executionStatus','missing')}`)")
 out += [f"- contractRef: `catalog.json#dashboardKey={dk}&widgetKey={w['key']}`",""]
 all_defs=w.get("authoritativeDefinitions",[])
 defs={d.get("metricKey"):d for d in all_defs if d.get("metricKey")}
 widget_defs=[d for d in all_defs if not d.get("metricKey") and d.get("text")]
 ms=sorted((m for m in w.get("metrics",[]) if not m.get("tombstone")),key=lambda m:(m.get("name",""),m.get("key","")))
 if ms:
  out += ["| Metric | metricKey | Unit | Definition | Source |","|---|---|---|---|---|"]
  for m in ms:
   d=defs.get(m.get("key"),{}); source=d.get("source",m.get("definitionSource",""))
   out.append(f"| {esc(m.get('name',''))} | metricKey=`{esc(m.get('key',''))}` | {esc(m.get('unit',''))} | {esc(d.get('text',m.get('authoritativeDefinition','')))} | {esc(source)} |")
  out.append("")
 if widget_defs:
  out += ["Authoritative widget definition / note:",""]
  for d in widget_defs:
   out.append(f"> {esc(d.get('text',''))}")
   if d.get("source"):out.append(f"> Source: `{esc(d['source'])}`")
   if d.get("observationNote"):out.append(f"> Observation note: {esc(d['observationNote'])}")
   if d.get("sourceReference"):out.append(f"> Source reference: `{esc(d['sourceReference'])}`")
   out.append("")
 for f in ("widgets","children"):
  for c in sorted(w.get(f,[]),key=lambda x:x.get("key","")):out+=widget(c,dk,ops,depth+1)
 return out
def render(cat,con):
 ops={c["operationId"]:c for c in con.get("contracts",[])}; groups={}
 for d in cat.get("dashboards",[]):groups.setdefault(tuple(d.get("menuPath",["Uncategorized"])),[]).append(d)
 out=["# Metric Catalog Index","","> Generated from canonical JSON. Retrieval only; execute through JSON contractRef.",""]
 for menu in sorted(groups):
  out += ["## Menu: "+" / ".join(menu),""]
  for d in sorted(groups[menu],key=lambda x:(x.get("name",""),x.get("key",""))):
   out += ["### Dashboard: "+str(d.get("name") or d["key"]),"",f"- dashboardKey: `{d['key']}`","- routes: "+", ".join(f"`{x}`" for x in sorted(d.get("routePatterns",[]))),""]
   if d.get("tabs"):
    out += ["#### Tabs",""]+tab_lines(d["tabs"])+[""]
   controls=sorted(d.get("controls",[]),key=lambda x:x.get("key",""))
   if controls:
    out += ["#### Controls / Parameters","","| Control | controlKey | Kind | Status | Options / protocol |","|---|---|---|---|---|"]
    for c in controls:
     opts=", ".join(option_text(x) for x in c.get("options",[]))
     protocol=c.get("optionProtocolStatus","")
     detail="; ".join(x for x in (opts,protocol) if x)
     out.append(f"| {esc(c.get('name',''))} | `{esc(c.get('key',''))}` | {esc(c.get('kind','unknown'))} | {esc(c.get('captureStatus','unknown'))} | {esc(detail)} |")
    out.append("")
   for w in sorted((x for x in d.get("widgets",[]) if not x.get("tombstone")),key=lambda x:x.get("key","")):out+=widget(w,d["key"],ops)
 return "\n".join(out).rstrip()+"\n"
def main(a):
 cat=json.loads(pathlib.Path(a.catalog).read_text(encoding="utf-8"));con=json.loads(pathlib.Path(a.contracts).read_text(encoding="utf-8"));p=pathlib.Path(a.out);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(render(cat,con),encoding="utf-8");print(p);return 0
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--catalog",required=True);p.add_argument("--contracts",required=True);p.add_argument("--out",required=True);raise SystemExit(main(p.parse_args()))
