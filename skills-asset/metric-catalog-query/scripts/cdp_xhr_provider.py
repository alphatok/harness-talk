#!/usr/bin/env python3
"""Read-only live provider that recompiles parameters and replays an authorized XHR via CDP."""
from __future__ import annotations

import base64
import hashlib
import json
import time
import urllib.request
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Mapping

from websockets.sync.client import connect


def _canon(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _shape(values: list[Any], depth: int = 0) -> dict[str, Any]:
    if not values:
        return {"type": "unknown"}
    kinds = {"null" if value is None else "array" if isinstance(value, list) else "object" if isinstance(value, dict) else type(value).__name__ for value in values}
    if len(kinds) != 1:
        return {"anyOf": sorted(kinds)}
    kind = next(iter(kinds))
    if depth >= 7:
        return {"type": kind}
    if kind == "object":
        keys = sorted({key for value in values for key in value})
        return {"type": "object", "required": [key for key in keys if all(key in value for value in values)],
                "properties": {key: _shape([value[key] for value in values if key in value], depth + 1) for key in keys}}
    if kind == "array":
        return {"type": "array", "items": _shape([item for value in values for item in value[:3]], depth + 1),
                "observedLengths": sorted({len(value) for value in values})[:20]}
    return {"type": kind}


def _fingerprint(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canon(_shape([value])).encode()).hexdigest()


class _CDP:
    def __init__(self, url: str):
        self.ws = connect(url, open_timeout=10, max_size=100 * 1024 * 1024)
        self.next_id = 1
        self.events: list[dict[str, Any]] = []

    def send(self, method: str, params: Mapping[str, Any] | None = None):
        message_id = self.next_id
        self.next_id += 1
        self.ws.send(json.dumps({"id": message_id, "method": method, "params": params or {}}))
        while True:
            event = json.loads(self.ws.recv())
            if event.get("id") == message_id:
                if event.get("error"):
                    raise RuntimeError(f"{method}: {event['error']}")
                return event.get("result", {})
            self.events.append(event)

    def collect(self, seconds: float):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            try:
                self.events.append(json.loads(self.ws.recv(timeout=max(0.1, deadline - time.monotonic()))))
            except TimeoutError:
                break


class CDPXhrProvider:
    def __init__(self, config: Mapping[str, Any]):
        self.port = int(config.get("port", 9222))
        self.data_home = Path(str(config.get("dataHome", "~/.metric_catalog"))).expanduser()
        self.today = date.fromisoformat(str(config["today"])) if config.get("today") else date.today()
        self.seed_seconds = float(config.get("seedSeconds", 10))

    def discover(self, selection: Mapping[str, Any], context: Mapping[str, Any]) -> Mapping[str, Any]:
        raise RuntimeError("targeted progressive discovery is not enabled for this adapter")

    def _semantic_fingerprint(self, widget_key: str) -> str | None:
        catalog = json.loads((self.data_home / "catalog" / "catalog.json").read_text(encoding="utf-8"))
        for dashboard in catalog.get("dashboards", []):
            for widget in dashboard.get("widgets", []):
                if widget.get("key") == widget_key:
                    return widget.get("semanticFingerprint")
        return None

    def _target(self, route: str) -> Mapping[str, Any]:
        targets = json.load(urllib.request.urlopen(f"http://127.0.0.1:{self.port}/json/list"))
        matches = [target for target in targets if target.get("type") == "page" and route in target.get("url", "")]
        if not matches:
            raise RuntimeError(f"authorized CDP target not found for route: {route}")
        return matches[0]

    def _date_range(self, parameters: Mapping[str, Any]) -> tuple[date, date] | None:
        preset = parameters.get("datePreset")
        if preset == "this_month":
            return self.today.replace(day=1), self.today
        if preset == "last_month":
            end = self.today.replace(day=1) - timedelta(days=1)
            return end.replace(day=1), end
        if parameters.get("relativeDays"):
            days = int(parameters["relativeDays"])
            return self.today - timedelta(days=max(0, days - 1)), self.today
        if parameters.get("startDate") and parameters.get("endDate"):
            return date.fromisoformat(str(parameters["startDate"])), date.fromisoformat(str(parameters["endDate"]))
        return None

    @staticmethod
    def _apply_dates(payload: dict[str, Any], period: tuple[date, date] | None) -> dict[str, str]:
        if not period:
            return {}
        start, end = (item.isoformat() for item in period)
        changed = False
        for group in payload.get("param", {}).get("filterFields", []):
            for child in group.get("children", []):
                filters = child.get("filters", [])
                if "日期" not in str(child.get("fieldId", "")) or len(filters) < 2:
                    continue
                filters[0]["value"], filters[1]["value"] = start, end
                changed = True
        if not changed:
            raise RuntimeError("date filter binding not found in the observed request")
        return {"startDate": start, "endDate": end}

    @staticmethod
    def _replay(cdp: _CDP, seed_request_id: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        start = len(cdp.events)
        cdp.send("Network.replayXHR", {"requestId": seed_request_id})
        cdp.collect(1)
        paused = next((event for event in cdp.events[start:] if event.get("method") == "Fetch.requestPaused"), None)
        if not paused:
            raise RuntimeError("XHR replay was not intercepted")
        params = paused["params"]
        post_data = base64.b64encode(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()).decode()
        cdp.send("Fetch.continueRequest", {"requestId": params["requestId"], "postData": post_data})
        network_id = params.get("networkId")
        cdp.collect(5)
        status, finished = None, False
        for event in cdp.events[start:]:
            event_params = event.get("params", {})
            if event_params.get("requestId") != network_id:
                continue
            if event.get("method") == "Network.responseReceived":
                status = event_params.get("response", {}).get("status")
            elif event.get("method") == "Network.loadingFinished":
                finished = True
        if not finished:
            raise RuntimeError("XHR replay response did not finish")
        response = cdp.send("Network.getResponseBody", {"requestId": network_id})
        raw = response.get("body", "")
        if response.get("base64Encoded"):
            raw = base64.b64decode(raw).decode("utf-8", "replace")
        return {"httpStatus": status, "body": json.loads(raw)}

    def execute(self, operation: Mapping[str, Any], parameters: Mapping[str, Any], binding: Mapping[str, Any], context: Mapping[str, Any]) -> Mapping[str, Any]:
        target = self._target(str(binding.get("route", "")))
        cdp = _CDP(str(target["webSocketDebuggerUrl"]))
        cdp.send("Page.enable")
        cdp.send("Network.enable", {"maxTotalBufferSize": 100_000_000, "maxResourceBufferSize": 50_000_000, "maxPostDataSize": 10_000_000})
        cdp.send("Page.reload", {"ignoreCache": False})
        cdp.collect(self.seed_seconds)

        widget_id = str(binding.get("widgetId", ""))
        seed_request_id, payload = None, None
        for event in cdp.events:
            if event.get("method") != "Network.requestWillBeSent":
                continue
            request = event.get("params", {}).get("request", {})
            if operation.get("path") not in request.get("url", ""):
                continue
            try:
                candidate = json.loads(request.get("postData") or "{}")
            except json.JSONDecodeError:
                continue
            info = candidate.get("widgetInfo") or {}
            if str(info.get("id") or info.get("widgetId") or "") == widget_id and not candidate.get("requestId"):
                seed_request_id, payload = event["params"]["requestId"], candidate
                break
        if not seed_request_id or not payload:
            raise RuntimeError(f"observed request template not found for widget {widget_id}")

        applied = self._apply_dates(payload, self._date_range(parameters))
        payload.pop("requestId", None)
        cdp.send("Fetch.enable", {"patterns": [{"urlPattern": f"*{operation.get('path')}*", "requestStage": "Request"}]})
        response = self._replay(cdp, seed_request_id, payload)
        for _ in range(20):
            body = response.get("body") or {}
            data = body.get("data") or {}
            result = data.get("result") or {}
            if response.get("httpStatus") != 200 or body.get("errcode") != 0 or data.get("status") != 2 or result.get("datas") is not None:
                break
            request_id = data.get("requestId") or result.get("requestId")
            if not request_id:
                break
            payload["requestId"] = request_id
            time.sleep(0.4)
            response = self._replay(cdp, seed_request_id, payload)
        cdp.send("Fetch.disable")

        body = response.get("body") or {}
        result = ((body.get("data") or {}).get("result") or {})
        fields = payload.get("param", {}).get("fields", [])
        labels = [str(field.get("displayName") or field.get("fieldId") or field.get("alias")) for field in fields]
        rows = [dict(zip(labels, row)) for row in (result.get("datas") or [])]
        totals: dict[str, float] = {}
        for index, field in enumerate(fields):
            label = labels[index]
            if "营业额" in label:
                totals[label] = round(sum(float(row[index]) for row in (result.get("datas") or []) if row[index] is not None), 2)
        raw_rows = result.get("datas")
        metas = result.get("metas")
        stable_schema = isinstance(body, dict) and isinstance(body.get("data"), dict) and isinstance(result, dict) and isinstance(raw_rows, list) and isinstance(metas, list)
        if stable_schema and raw_rows:
            stable_schema = all(isinstance(row, list) and len(row) == len(metas) == len(fields) for row in raw_rows)
        success = response.get("httpStatus") == 200 and body.get("errcode") == 0 and result.get("status") == 1 and stable_schema
        observed_schema = _fingerprint(body)
        contract_schema = operation.get("responseSchemaFingerprint") or operation.get("schemaFingerprint")
        return {
            "httpStatus": response.get("httpStatus"),
            "businessSuccess": success,
            "data": {"rows": rows, "totals": totals},
            "schemaFingerprint": contract_schema if stable_schema else observed_schema,
            "semanticFingerprint": self._semantic_fingerprint(str(binding.get("widgetTemplateKey", ""))),
            "appliedFilters": {**parameters, **applied},
            "provenance": {"source": "chrome_cdp_xhr_replay", "operationId": operation.get("operationId"),
                           "widgetId": widget_id, "datasetId": binding.get("datasetId"), "observedPeriod": applied,
                           "schemaValidation": "stable_structure", "observedSchemaFingerprint": observed_schema},
        }


def create_provider(config: Mapping[str, Any]) -> CDPXhrProvider:
    return CDPXhrProvider(config)
