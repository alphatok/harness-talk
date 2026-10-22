from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


SCRIPTS = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import capture_catalog  # noqa: E402
import capture_cdp_network  # noqa: E402
import merge_catalog  # noqa: E402
import render_index  # noqa: E402
import validate_catalog  # noqa: E402


def capture(capture_id: str, schema: str = "sha256:a") -> dict:
    return {
        "schemaVersion": "1.0",
        "kind": "metric-catalog-capture-run",
        "captureId": capture_id,
        "observedAt": "2026-09-02T00:00:00Z",
        "entryUrl": "https://example.test/dashboard",
        "scope": "menu",
        "idMode": "reuse",
        "browser": "in_app",
        "scopeKey": "test-scope",
        "status": "complete",
        "dashboards": [
            {
                "key": "crm.customer.overview",
                "name": "客户总览",
                "menuPath": ["数据", "CRM"],
                "routePatterns": ["/dashboard/customer"],
                "captureStatus": "captured",
                "widgets": [
                    {
                        "key": "crm.customer.overview.lifecycle",
                        "kind": "data_leaf",
                        "title": "客户生命周期",
                        "captureStatus": "captured",
                        "helpExpected": True,
                        "definitionStatus": "captured",
                        "directOperationRefs": ["customer.lifecycle.query"],
                        "metrics": [{"key": "customer.active", "name": "活跃客户数"}],
                        "authoritativeDefinitions": [
                            {"metricKey": "customer.active", "text": "活跃客户口径原文"}
                        ],
                    }
                ],
            }
        ],
        "contracts": [
            {
                "operationId": "customer.lifecycle.query",
                "method": "POST",
                "path": "/api/query",
                "schemaFingerprint": schema,
                "executionStatus": "executable",
                "verification": {
                    "http200": True,
                    "businessSuccess": True,
                    "responseSchemaMatched": True,
                    "targetFieldsProjected": True,
                },
            }
        ],
        "instanceBindings": [],
        "actions": [],
        "blockers": [],
        "redaction": {"credentialsPersisted": False, "rawBusinessRowsPersisted": False},
    }


class CapturePipelineTest(unittest.TestCase):
    def test_cdp_semantic_metadata_preserves_tooltip_text(self) -> None:
        body = {
            "data": {
                "widgetRespVos": [{
                    "widgetId": "w1",
                    "setting": json.dumps({
                        "title": "业绩金额",
                        "tooltip": "销售业绩与发货业绩按页面口径统计。",
                    }, ensure_ascii=False),
                }],
                "schemaRespVo": {"name": "门店业绩"},
            }
        }
        metadata = capture_cdp_network.semantic_metadata(body)
        self.assertEqual(metadata["widgets"][0]["titles"], ["业绩金额"])
        self.assertEqual(
            metadata["widgets"][0]["authoritativeDefinitionCandidates"][0]["text"],
            "销售业绩与发货业绩按页面口径统计。",
        )

    def test_goal_action_does_not_embed_page_specific_javascript(self) -> None:
        expression = capture_cdp_network.action_expression({
            "kind": "click", "text": "市", "withinText": "客户收货区域分布", "occurrence": 1,
        })
        self.assertIn("客户收货区域分布", expression)
        self.assertIn("occurrence", expression)
        self.assertNotIn("document.cookie", expression)

    def test_capture_merge_render_validate_is_complete(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            run = home / "run.json"
            capture_catalog.write(run, capture("run-1"))
            self.assertEqual(capture_catalog.validate(json.loads(run.read_text())), [])
            self.assertEqual(merge_catalog.main(SimpleNamespace(data_home=str(home), capture_runs=[str(run)])), 0)
            self.assertTrue((home / "captures/run-1/capture-run.json").exists())
            catalog = json.loads((home / "catalog/catalog.json").read_text())
            contracts = json.loads((home / "catalog/contracts.json").read_text())
            index = render_index.render(catalog, contracts)
            errors, coverage = validate_catalog.check(catalog, contracts, index)
            self.assertEqual(errors, [])
            self.assertEqual(coverage["status"], "complete")
            self.assertIn("dashboardKey: `crm.customer.overview`", index)
            self.assertIn("metricKey=`customer.active`", index)
            self.assertEqual(catalog["dashboards"][0]["widgets"][0]["executionStatus"], "executable")

    def test_repeated_merge_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            run = home / "run.json"
            capture_catalog.write(run, capture("run-1"))
            args = SimpleNamespace(data_home=str(home), capture_runs=[str(run)])
            merge_catalog.main(args)
            merge_catalog.main(args)
            catalog = json.loads((home / "catalog/catalog.json").read_text())
            self.assertEqual(len(catalog["dashboards"]), 1)
            self.assertEqual(len(catalog["captureHistory"]), 1)

    def test_schema_conflict_forces_revalidation(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            first, second = home / "first.json", home / "second.json"
            capture_catalog.write(first, capture("run-1", "sha256:a"))
            newer = capture("run-2", "sha256:b")
            newer["observedAt"] = "2026-09-03T00:00:00Z"
            capture_catalog.write(second, newer)
            merge_catalog.main(SimpleNamespace(data_home=str(home), capture_runs=[str(first), str(second)]))
            contracts = json.loads((home / "catalog/contracts.json").read_text())
            self.assertEqual(contracts["contracts"][0]["executionStatus"], "needs_revalidation")
            catalog = json.loads((home / "catalog/catalog.json").read_text())
            self.assertEqual(catalog["dashboards"][0]["widgets"][0]["executionStatus"], "needs_revalidation")

    def test_discovered_data_widget_without_operation_is_a_blocker_not_an_error(self) -> None:
        run = capture("run-no-operation")
        run["dashboards"][0]["widgets"][0]["directOperationRefs"] = []
        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            path = home / "run.json"
            capture_catalog.write(path, run)
            merge_catalog.main(SimpleNamespace(data_home=str(home), capture_runs=[str(path)]))
            catalog = json.loads((home / "catalog/catalog.json").read_text())
            contracts = json.loads((home / "catalog/contracts.json").read_text())
            index = render_index.render(catalog, contracts)
            errors, coverage = validate_catalog.check(catalog, contracts, index)
            self.assertEqual(errors, [])
            self.assertEqual(coverage["status"], "incomplete")
            self.assertIn("data operation not discovered", {item["reason"] for item in coverage["blockers"]})

    def test_widget_level_authoritative_definition_is_rendered(self) -> None:
        run = capture("run-widget-definition")
        widget = run["dashboards"][0]["widgets"][0]
        widget["metrics"] = []
        widget["authoritativeDefinitions"] = [{
            "text": "页面问号中的完整权威说明",
            "sourceReference": "customer_overview.lifecycle",
            "observationNote": "按页面原文保留",
        }]
        catalog = {"dashboards": run["dashboards"]}
        contracts = {"contracts": run["contracts"]}
        index = render_index.render(catalog, contracts)
        self.assertIn("Authoritative widget definition", index)
        self.assertIn("页面问号中的完整权威说明", index)
        self.assertIn("按页面原文保留", index)

    def test_verified_operation_refs_override_historical_generic_refs(self) -> None:
        run = capture("run-verified-closure")
        widget = run["dashboards"][0]["widgets"][0]
        widget["directOperationRefs"] = ["customer.lifecycle.generic"]
        widget["verifiedOperationRefs"] = ["customer.lifecycle.query"]
        run["contracts"].append({
            "operationId": "customer.lifecycle.generic",
            "method": "POST",
            "path": "/generic",
            "verification": {key: False for key in capture_catalog.CHECKS},
            "executionStatus": "needs_revalidation",
        })
        catalog = {"dashboards": run["dashboards"]}
        contracts = {"contracts": run["contracts"]}
        index = render_index.render(catalog, contracts)
        errors, coverage = validate_catalog.check(catalog, contracts, index)
        self.assertEqual(errors, [])
        self.assertEqual(coverage["counts"]["executableDataLeaves"], 1)
        self.assertIn("verified operation", index)


if __name__ == "__main__":
    unittest.main()
