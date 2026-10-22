#!/usr/bin/env python3
"""Natural-language metric resolver with injectable read-only providers."""
from __future__ import annotations

import argparse
import importlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Protocol


class QueryFailure(Exception): category = "error"
class BindingDrift(QueryFailure): category = "binding_drift"
class SchemaDrift(QueryFailure): category = "schema_drift"
class AuthFailure(QueryFailure): category = "auth"
class AuthorizationFailure(QueryFailure): category = "authorization"
class RateLimitFailure(QueryFailure): category = "rate_limit"
class NetworkFailure(QueryFailure): category = "network"


class Provider(Protocol):
    def discover(self, selection: Mapping[str, Any], context: Mapping[str, Any]) -> Mapping[str, Any]: ...
    def execute(self, operation: Mapping[str, Any], parameters: Mapping[str, Any], binding: Mapping[str, Any], context: Mapping[str, Any]) -> Mapping[str, Any]: ...


@dataclass(frozen=True)
class Candidate:
    dashboard: Mapping[str, Any]
    widget: Mapping[str, Any]
    metric: Mapping[str, Any]
    score: float

    def public(self) -> dict[str, Any]:
        return {"dashboardKey": self.dashboard.get("key"), "dashboard": self.dashboard.get("name"),
                "widgetKey": self.widget.get("key"), "widget": self.widget.get("title", self.widget.get("name")),
                "metricKey": self.metric.get("key"), "metric": self.metric.get("name"), "score": round(self.score, 3)}


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists() and default is not None: return default
    with path.open(encoding="utf-8") as handle: return json.load(handle)


def intent(question: str, output: str) -> str:
    q = question.lower()
    if output == "chart" or any(x in q for x in ("可视化", "画图", "图表", "趋势图")): return "visualize"
    if any(x in q for x in ("定义", "口径", "含义", "什么意思", "怎么计算", "说明")): return "definition"
    if any(x in q for x in ("对比", "比较", "同比", "环比", "分别")): return "compare"
    return "data"


def terms(text: str) -> set[str]:
    text = re.sub(r"\s+", "", text.lower())
    result = set(re.findall(r"[a-z0-9_.-]+", text))
    han = "".join(re.findall(r"[\u4e00-\u9fff]", text))
    result |= {han[i:i+n] for n in (2, 3, 4) for i in range(max(0, len(han)-n+1))}
    return {x for x in result if x}


def flat(value: Any) -> str:
    if isinstance(value, str): return value
    if isinstance(value, list): return " ".join(flat(x) for x in value)
    return ""


def index_hints(index_text: str, question: str) -> set[str]:
    qterms, hints = terms(question), set()
    for line in index_text.splitlines():
        if qterms & terms(line):
            hints.update(re.findall(r"(?:dashboard|widget|metric)Key\s*[:=]\s*`?([\w.-]+)", line, re.I))
    return hints


def rank(catalog: Mapping[str, Any], question: str, hints: set[str]) -> list[Candidate]:
    q, qt, found = question.lower(), terms(question), []
    for dashboard in catalog.get("dashboards", []):
        if dashboard.get("tombstone"): continue
        dt = flat([dashboard.get("key", ""), dashboard.get("name", ""), dashboard.get("aliases", []), dashboard.get("menuPath", [])]).lower()
        for widget in dashboard.get("widgets", []):
            if widget.get("tombstone"): continue
            wt = flat([widget.get("key", ""), widget.get("title", widget.get("name", "")), widget.get("aliases", []), widget.get("hierarchyPath", []), [x.get("text", "") for x in widget.get("authoritativeDefinitions", []) if isinstance(x, Mapping)]]).lower()
            metrics = widget.get("metrics") or [{"key": widget.get("key"), "name": widget.get("title", widget.get("name", ""))}]
            for metric in metrics:
                if metric.get("tombstone"): continue
                mt = flat([metric.get("key", ""), metric.get("name", ""), metric.get("aliases", []), metric.get("authoritativeDefinition", metric.get("definition", ""))]).lower()
                score = sum(weight * len(qt & terms(text)) / max(1, len(qt)) for text, weight in ((mt, 7), (wt, 4), (dt, 5)))
                for exact, weight in ((metric.get("name"), 8), (widget.get("title", widget.get("name")), 5), (dashboard.get("name"), 6)):
                    if exact and str(exact).lower() in q: score += weight
                if {str(dashboard.get("key")), str(widget.get("key")), str(metric.get("key"))} & hints: score += 3
                if score > 0: found.append(Candidate(dashboard, widget, metric, score))
    return sorted(found, key=lambda x: (-x.score, str(x.dashboard.get("key")), str(x.widget.get("key")), str(x.metric.get("key"))))


def route_executable(candidates: list[Candidate], query_intent: str) -> list[Candidate]:
    """Route a metric defined on a non-data parent to a verified semantic child."""
    if query_intent == "definition":
        return candidates
    routed: dict[tuple[str, str, str], Candidate] = {}
    for candidate in candidates:
        selected = candidate
        if candidate.widget.get("executionStatus") != "executable":
            metric_name = str(candidate.metric.get("name") or "").strip().lower()
            compatible = []
            for widget in candidate.dashboard.get("widgets", []):
                if widget.get("executionStatus") != "executable" or widget.get("tombstone"):
                    continue
                semantics = flat([widget.get("title", widget.get("name", "")), widget.get("aliases", [])]).lower()
                if metric_name and metric_name in semantics:
                    compatible.append(widget)
            if compatible:
                compatible.sort(key=lambda item: (str(item.get("key")), str(item.get("title", item.get("name", "")))))
                selected = Candidate(candidate.dashboard, compatible[0], candidate.metric, candidate.score)
        key = (str(selected.dashboard.get("key")), str(selected.widget.get("key")), str(selected.metric.get("key")))
        if key not in routed or selected.score > routed[key].score:
            routed[key] = selected
    return sorted(routed.values(), key=lambda x: (-x.score, str(x.dashboard.get("key")), str(x.widget.get("key")), str(x.metric.get("key"))))


def parameters(question: str, extra: Mapping[str, Any]) -> dict[str, Any]:
    result, q = dict(extra), question.lower()
    match = re.search(r"最近\s*(\d+)\s*天", q)
    if match: result.setdefault("relativeDays", int(match.group(1)))
    match = re.search(r"(?:top|前)\s*(\d+)", q, re.I)
    if match: result.setdefault("topN", int(match.group(1)))
    for label, value in (("按日", "day"), ("按周", "week"), ("按月", "month")):
        if label in q: result.setdefault("granularity", value)
    if "本月" in q: result.setdefault("datePreset", "this_month")
    elif "上月" in q: result.setdefault("datePreset", "last_month")
    return result


def contract_parameters(question: str, op: Mapping[str, Any], base: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, resolver in op.get("dynamicOptionResolvers", {}).items():
        if key in result: continue
        for pattern in resolver.get("naturalLanguagePatterns", []):
            match = re.search(pattern, question, re.I)
            if match:
                result[key] = match.groupdict().get("value") or match.group(1)
                break
        if key in result: continue
        lowered = str(key).lower()
        if "member" in lowered and any(x in lowered for x in ("grade", "level")):
            match = re.search(r"(?:最近\s*\d+\s*天|本月|上月|会员等级(?:为|是)?|等级(?:为|是)?)([\u4e00-\u9fffA-Za-z0-9_-]{1,12}会员)", question)
            if match: result[key] = match.group(1)
    return result


def operation_map(contracts: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    value = contracts.get("operations", contracts.get("contracts", contracts))
    if isinstance(value, dict): return {str(k): v for k, v in value.items() if isinstance(v, dict)}
    return {str(x["operationId"]): x for x in value if isinstance(x, dict) and x.get("operationId")}


def operation(candidate: Candidate, operations: Mapping[str, Mapping[str, Any]]) -> tuple[str, Mapping[str, Any]]:
    refs = candidate.widget.get("directOperationRefs") or candidate.widget.get("operationRefs") or []
    if not refs: raise QueryFailure("selected widget has no direct operation reference")
    scoped = [f"{ref}.{candidate.dashboard.get('key')}" for ref in refs]
    candidates = list(dict.fromkeys([str(ref) for ref in refs] + scoped))
    for ref in candidates:
        contract = operations.get(ref)
        if contract and contract.get("executionStatus") == "executable":
            return ref, contract
    existing = [ref for ref in candidates if ref in operations]
    if existing: raise QueryFailure("no referenced operation is executable: " + ", ".join(existing))
    raise QueryFailure("operation contract not found: " + ", ".join(candidates))


def binding(bindings: Mapping[str, Any], candidate: Candidate) -> tuple[Mapping[str, Any], str]:
    values = bindings.get("widgets", bindings.get("bindings", {}))
    if isinstance(values, dict):
        for key in (str(candidate.widget.get("key")), str(candidate.dashboard.get("key"))):
            if key in values: return values[key], "instance_cache"
    elif isinstance(values, list):
        for value in values:
            if not isinstance(value, Mapping): continue
            dashboard_match = value.get("dashboardTemplateKey") in (None, candidate.dashboard.get("key"))
            widget_match = value.get("widgetTemplateKey") in (None, candidate.widget.get("key"))
            nested = value.get("widgetBindings", {})
            if dashboard_match and isinstance(nested, Mapping) and str(candidate.widget.get("key")) in nested:
                return nested[str(candidate.widget.get("key"))], "instance_cache"
            if dashboard_match and isinstance(nested, list):
                for child in nested:
                    if isinstance(child, Mapping) and child.get("widgetTemplateKey") == candidate.widget.get("key"):
                        return {**value, **child}, "instance_cache"
            if dashboard_match and widget_match and (value.get("widgetId") is not None or value.get("datasetId") is not None):
                return value, "instance_cache"
    reusable = candidate.widget.get("reusableBinding") or candidate.widget.get("runtimeBinding") or {}
    return reusable, "template_reuse" if reusable else "none"


def resolve_parameters(provider: Provider, op: Mapping[str, Any], params: Mapping[str, Any], current: Mapping[str, Any], context: Mapping[str, Any]) -> dict[str, Any]:
    resolved = dict(params)
    missing = [str(key) for key in op.get("requiredParameters", []) if key not in resolved]
    if missing: raise QueryFailure("required parameters missing: " + ", ".join(missing))
    resolvers = op.get("dynamicOptionResolvers", {})
    for key, resolver in resolvers.items():
        if key not in resolved: continue
        method = getattr(provider, "resolve_option", None)
        if method is None: raise QueryFailure(f"dynamic option resolver unavailable: {key}")
        resolved[key] = method(resolver, resolved[key], current, context)
    return resolved


def metric_definition(candidate: Candidate) -> Any:
    direct = candidate.metric.get("authoritativeDefinition", candidate.metric.get("definition"))
    if direct is not None: return direct
    widget_level = []
    for item in candidate.widget.get("authoritativeDefinitions", []):
        if item.get("metricKey") == candidate.metric.get("key"):
            return item.get("text")
        if not item.get("metricKey") and item.get("text"):
            widget_level.append(str(item["text"]))
    return "\n\n".join(widget_level) if widget_level else None


def validate(response: Mapping[str, Any], op: Mapping[str, Any], candidate: Candidate, params: Mapping[str, Any]) -> Any:
    status = int(response.get("httpStatus", 0))
    if status == 401: raise AuthFailure("HTTP 401")
    if status == 403: raise AuthorizationFailure("HTTP 403")
    if status == 429: raise RateLimitFailure("HTTP 429")
    if status != 200: raise QueryFailure(f"unexpected HTTP status: {status}")
    if response.get("businessSuccess") is not True:
        if response.get("errorCategory") == "binding_drift": raise BindingDrift("runtime binding rejected")
        raise QueryFailure("business success rule failed")
    expected = op.get("responseSchemaFingerprint") or op.get("schemaFingerprint")
    if expected and response.get("schemaFingerprint") != expected: raise SchemaDrift("response schema fingerprint mismatch")
    expected = candidate.widget.get("semanticFingerprint") or op.get("semanticFingerprint")
    if expected and response.get("semanticFingerprint") != expected: raise SchemaDrift("widget semantic fingerprint mismatch")
    applied = response.get("appliedFilters", {})
    missing = [x for x in op.get("requiredAppliedFilters", []) if x in params and x not in applied]
    if missing: raise SchemaDrift("filters not proven applied: " + ", ".join(missing))
    return response.get("data")


def dig(value: Any, path: str) -> Any:
    for part in path.split(".") if path else []:
        if not isinstance(value, Mapping) or part not in value: raise SchemaDrift(f"projection field missing: {path}")
        value = value[part]
    return value


def normalize(data: Any, op: Mapping[str, Any], candidate: Candidate) -> dict[str, Any]:
    mapping = op.get("responseMapping") or candidate.widget.get("responseMapping") or {}
    rows = dig(data, mapping["rows"]) if mapping.get("rows") else data if isinstance(data, list) else data.get("rows", []) if isinstance(data, Mapping) else []
    totals = dig(data, mapping["totals"]) if mapping.get("totals") else data.get("totals", {}) if isinstance(data, Mapping) else {}
    metric = candidate.metric
    return {"dimensions": op.get("dimensions", []), "measures": op.get("measures", [{"key": metric.get("key"), "label": metric.get("name"), "unit": metric.get("unit")}]),
            "rows": rows, "totals": totals, "units": op.get("units", {}), "timezone": op.get("timezone", "Asia/Shanghai"),
            "metricDefinitions": [{"key": metric.get("key"), "name": metric.get("name"), "definition": metric_definition(candidate), "provenance": metric.get("provenance", candidate.widget.get("provenance", []))}]}


def present(output: str, query_intent: str, data: Mapping[str, Any]) -> tuple[dict[str, Any], list[str]]:
    mode, warnings = output, []
    if mode == "auto":
        dims, rows = data.get("dimensions", []), data.get("rows", [])
        mode = "chart" if query_intent == "visualize" or any(x.get("type") in ("date", "datetime", "time") for x in dims) else "table" if len(rows) > 1 or len(dims) > 1 else "summary"
    result = {"mode": mode}
    if mode == "chart":
        dims = data.get("dimensions", [])
        if not dims:
            result["mode"] = "summary"; warnings.append("chart downgraded because no dimension is exposed")
        else:
            result["chartSpec"] = {"type": "line" if dims[0].get("type") in ("date", "datetime", "time") else "bar", "x": dims[0].get("key"), "series": [x.get("key") for x in data.get("measures", [])]}
    return result, warnings


def result(status: str, **updates: Any) -> dict[str, Any]:
    value = {"status": status, "selection": [], "resolvedParameters": {}, "bindingSource": None, "fallbackUsed": False, "normalizedData": None, "presentation": None, "provenance": [], "warnings": []}
    value.update(updates); return value


def query_metric(*, question: str, catalog: Mapping[str, Any], contracts: Mapping[str, Any], index_text: str = "", bindings: Mapping[str, Any] | None = None, context: Mapping[str, Any] | None = None, id_mode: str = "reuse", output: str = "auto", extra_filters: Mapping[str, Any] | None = None, provider: Provider | None = None, min_score: float = 7.0, ambiguity_margin: float = 1.5, dry_run: bool = False) -> dict[str, Any]:
    if id_mode not in {"reuse", "progressive"}: return result("blocked", warnings=["id_mode must be reuse or progressive"])
    query_intent, params = intent(question, output), parameters(question, extra_filters or {})
    candidates = route_executable(rank(catalog, question, index_hints(index_text, question)), query_intent)
    if not candidates or candidates[0].score < min_score:
        return result("clarification_required", resolvedParameters=params, presentation={"intent": query_intent, "candidates": [x.public() for x in candidates[:5]]}, warnings=["no sufficiently confident metric match"])
    first = candidates[0]
    if len(candidates) > 1 and first.score-candidates[1].score <= ambiguity_margin and (first.dashboard.get("key"), first.widget.get("key")) != (candidates[1].dashboard.get("key"), candidates[1].widget.get("key")):
        return result("clarification_required", resolvedParameters=params, presentation={"intent": query_intent, "candidates": [x.public() for x in candidates[:5]]}, warnings=["multiple dashboard/widget matches are materially tied"])
    selected = [first]
    if query_intent == "compare":
        selected += [x for x in candidates[1:] if x.score >= min_score][:2]
    selection = [x.public() for x in selected]
    if query_intent == "definition":
        definitions = [{"selection": x.public(), "definition": metric_definition(x), "provenance": x.metric.get("provenance", x.widget.get("provenance", []))} for x in selected]
        return result("success", selection=selection, resolvedParameters=params, normalizedData={"metricDefinitions": definitions}, presentation={"mode": "definition", "intent": query_intent}, provenance=[p for x in definitions for p in x["provenance"]])
    ops, plans = operation_map(contracts), []
    for item in selected:
        if item.widget.get("executionStatus") != "executable": return result("blocked", selection=selection, resolvedParameters=params, warnings=[f"widget is not executable: {item.widget.get('key')}"])
        try: ref, op = operation(item, ops)
        except QueryFailure as exc: return result("blocked", selection=selection, resolvedParameters=params, warnings=[str(exc)])
        plans.append((item, ref, op))
        params = contract_parameters(question, op, params)
    if dry_run: return result("dry_run", selection=selection, resolvedParameters=params, presentation={"intent": query_intent, "output": output, "operations": [x[1] for x in plans]})
    if provider is None: return result("blocked", selection=selection, resolvedParameters=params, warnings=["no provider injected"])
    blocks, provenance, sources, fallback, runtime_warnings = [], [], [], False, []
    for item, ref, op in plans:
        current, source = binding(bindings or {}, item)
        if id_mode == "progressive":
            try: current, source = provider.discover(item.public(), context or {}), "progressive"
            except Exception as exc: return result("error", selection=selection, resolvedParameters=params, warnings=[f"progressive discovery failed: {type(exc).__name__}"])
        retried = False
        while True:
            try:
                wire_params = resolve_parameters(provider, op, params, current, context or {})
                response = provider.execute(op, wire_params, current, context or {})
                validated_data = validate(response, op, item, wire_params)
                block = normalize(validated_data, op, item)
                if output == "raw":
                    # Returned only to the current caller; this runner never writes it.
                    block["rawData"] = validated_data
                blocks.append(block)
                if source == "progressive":
                    persist = getattr(provider, "persist_binding", None)
                    if persist is not None:
                        try: persist(item.public(), current, context or {})
                        except Exception as exc: runtime_warnings.append(f"binding cache update failed: {type(exc).__name__}")
                if response.get("provenance"): provenance.append(response["provenance"])
                sources.append(source); break
            except (BindingDrift, SchemaDrift) as exc:
                if id_mode != "reuse" or retried: return result("error", selection=selection, resolvedParameters=params, bindingSource=source, fallbackUsed=fallback, warnings=[str(exc)])
                retried = fallback = True
                try: current, source = provider.discover(item.public(), context or {}), "progressive"
                except Exception as discovery: return result("error", selection=selection, resolvedParameters=params, fallbackUsed=True, warnings=[f"progressive discovery failed: {type(discovery).__name__}"])
            except (AuthFailure, AuthorizationFailure, RateLimitFailure, NetworkFailure) as exc:
                return result("error", selection=selection, resolvedParameters=params, bindingSource=source, fallbackUsed=fallback, warnings=[f"{exc.category}: {exc}"])
            except Exception as exc:
                return result("error", selection=selection, resolvedParameters=params, bindingSource=source, fallbackUsed=fallback, warnings=[f"provider validation failed: {type(exc).__name__}: {str(exc)[:120]}"])
    normalized = blocks[0] if len(blocks) == 1 else {"blocks": blocks}
    if len(blocks) == 1:
        presentation, warnings = present(output, query_intent, blocks[0])
    else:
        signatures={(json.dumps(x.get("dimensions", []),sort_keys=True,ensure_ascii=False),json.dumps(x.get("units", {}),sort_keys=True,ensure_ascii=False),x.get("timezone")) for x in blocks}
        warnings=[] if len(signatures)==1 else ["comparison blocks have incompatible dimensions, units, or timezone and were kept separate"]
        presentation={"mode": "comparison", "blocks": len(blocks), "joined": False}
    return result("success", selection=selection, resolvedParameters=params, bindingSource=sources[0] if len(set(sources)) == 1 else "mixed", fallbackUsed=fallback, normalizedData=normalized, presentation={"intent": query_intent, **presentation}, provenance=provenance, warnings=runtime_warnings+warnings)


class FixtureProvider:
    def __init__(self, fixture: Mapping[str, Any]): self.fixture, self.calls, self.discoveries = fixture, 0, 0
    def discover(self, selection: Mapping[str, Any], context: Mapping[str, Any]) -> Mapping[str, Any]: self.discoveries += 1; return self.fixture.get("discoveredBinding", {})
    def resolve_option(self, resolver: Mapping[str, Any], label: str, binding: Mapping[str, Any], context: Mapping[str, Any]) -> Any:
        resolver_key = str(resolver.get("resolver") or resolver.get("operationId") or resolver.get("key") or "")
        values = self.fixture.get("optionValues", {}).get(resolver_key, {})
        if label not in values: raise QueryFailure(f"dynamic option not found: {resolver_key}/{label}")
        value = values[label]
        if isinstance(value, list):
            if len(value) != 1: raise QueryFailure(f"dynamic option is ambiguous: {resolver_key}/{label}")
            return value[0]
        return value
    def execute(self, operation: Mapping[str, Any], parameters: Mapping[str, Any], binding: Mapping[str, Any], context: Mapping[str, Any]) -> Mapping[str, Any]:
        responses = self.fixture.get("responses", []); self.calls += 1
        if not responses: raise QueryFailure("fixture has no responses")
        response = responses[min(self.calls-1, len(responses)-1)]
        if response.get("raise"):
            cls = {"binding_drift": BindingDrift, "schema_drift": SchemaDrift, "auth": AuthFailure, "authorization": AuthorizationFailure, "rate_limit": RateLimitFailure, "network": NetworkFailure}.get(response["raise"], QueryFailure)
            raise cls(response.get("message", response["raise"]))
        return response


def load_adapter(spec: str, config: Mapping[str, Any]) -> Provider:
    module, factory = spec.split(":", 1); return getattr(importlib.import_module(module), factory)(config)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-home", default="~/.metric_catalog"); parser.add_argument("--question", required=True); parser.add_argument("--scope-key")
    parser.add_argument("--id-mode", choices=("reuse", "progressive"), default="reuse"); parser.add_argument("--output", choices=("auto", "raw", "table", "summary", "chart"), default="auto")
    parser.add_argument("--extra-filters", default="{}"); parser.add_argument("--provider", choices=("dry-run", "fixture", "adapter"), default="dry-run")
    parser.add_argument("--fixture"); parser.add_argument("--adapter"); parser.add_argument("--adapter-config", default="{}")
    args = parser.parse_args(argv); home = Path(args.data_home).expanduser()
    catalog, contracts = load_json(home/"catalog"/"catalog.json"), load_json(home/"catalog"/"contracts.json")
    index_path = home/"index"/"metrics-index.md"; index_text = index_path.read_text(encoding="utf-8") if index_path.exists() else ""
    bindings = load_json(home/"instances"/args.scope_key/"bindings.json", {}) if args.scope_key else {}
    provider: Provider | None = None
    if args.provider == "fixture":
        if not args.fixture: parser.error("--fixture is required")
        provider = FixtureProvider(load_json(Path(args.fixture)))
    elif args.provider == "adapter":
        if not args.adapter: parser.error("--adapter is required")
        provider = load_adapter(args.adapter, json.loads(args.adapter_config))
    value = query_metric(question=args.question, catalog=catalog, contracts=contracts, index_text=index_text, bindings=bindings,
                         id_mode=args.id_mode, output=args.output, extra_filters=json.loads(args.extra_filters), provider=provider, dry_run=args.provider == "dry-run")
    json.dump(value, sys.stdout, ensure_ascii=False, indent=2); print()
    return 0 if value["status"] in ("success", "partial", "clarification_required", "dry_run") else 2


if __name__ == "__main__": raise SystemExit(main())
