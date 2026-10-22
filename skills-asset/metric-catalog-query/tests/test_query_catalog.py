from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
import query_catalog as query  # noqa: E402


def catalog(status: str = "executable") -> dict:
    return {
        "dashboards": [
            {
                "key": "crm.member.contribution",
                "name": "会员贡献",
                "menuPath": ["数据", "CRM", "会员分析"],
                "widgets": [
                    {
                        "key": "crm.member.contribution.core",
                        "title": "会员核心指标",
                        "kind": "data_leaf",
                        "executionStatus": status,
                        "semanticFingerprint": "sha256:semantic",
                        "directOperationRefs": ["member.core.query"],
                        "reusableBinding": {"widgetId": "shared-widget"},
                        "metrics": [
                            {"key": "member.repurchase_rate", "name": "复购率", "unit": "%"}
                        ],
                        "authoritativeDefinitions": [
                            {"metricKey": "member.repurchase_rate", "text": "支付客户中的复购客户比例"}
                        ],
                    }
                ],
            }
        ]
    }


def contracts(status: str = "executable", dynamic: bool = False) -> dict:
    operation = {
        "operationId": "member.core.query",
        "executionStatus": status,
        "schemaFingerprint": "sha256:schema",
        "semanticFingerprint": "sha256:semantic",
        "requiredAppliedFilters": ["relativeDays"],
        "responseMapping": {"rows": "rows"},
        "dimensions": [{"key": "date", "type": "date"}],
        "measures": [{"key": "member.repurchase_rate", "unit": "%"}],
    }
    if dynamic:
        operation["dynamicOptionResolvers"] = {"memberGrade": {"resolver": "member-grade"}}
    return {"contracts": [operation]}


class Provider:
    def __init__(self, responses: list[dict]) -> None:
        self.responses = responses
        self.calls = 0
        self.discoveries = 0
        self.persisted = 0
        self.last_parameters = {}

    def discover(self, selection, context):
        self.discoveries += 1
        return {"widgetId": "current-widget"}

    def resolve_option(self, resolver, label, binding, context):
        return {"黄金会员": "grade-1"}[label]

    def persist_binding(self, selection, binding, context):
        self.persisted += 1

    def execute(self, operation, parameters, binding, context):
        self.last_parameters = dict(parameters)
        response = self.responses[self.calls]
        self.calls += 1
        if response.get("raise") == "binding_drift":
            raise query.BindingDrift("stale")
        if response.get("raise") == "authorization":
            raise query.AuthorizationFailure("forbidden")
        return response


def ok() -> dict:
    return {
        "httpStatus": 200,
        "businessSuccess": True,
        "schemaFingerprint": "sha256:schema",
        "semanticFingerprint": "sha256:semantic",
        "appliedFilters": {"relativeDays": 7},
        "data": {"rows": [{"date": "2026-09-01", "member.repurchase_rate": 0.2}]},
    }


class QueryCatalogTest(unittest.TestCase):
    def test_definition_does_not_call_provider(self) -> None:
        provider = Provider([])
        result = query.query_metric(question="会员贡献复购率是什么意思", catalog=catalog("needs_revalidation"), contracts=contracts("needs_revalidation"), provider=provider)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["normalizedData"]["metricDefinitions"][0]["definition"], "支付客户中的复购客户比例")
        self.assertEqual(provider.calls, 0)

    def test_widget_level_authoritative_definition_is_returned(self) -> None:
        source = catalog("needs_revalidation")
        widget = source["dashboards"][0]["widgets"][0]
        widget["metrics"] = []
        widget["authoritativeDefinitions"] = [{"text": "页面问号中的完整权威说明"}]
        provider = Provider([])
        result = query.query_metric(
            question="会员核心指标是什么意思",
            catalog=source,
            contracts=contracts("needs_revalidation"),
            provider=provider,
        )
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["normalizedData"]["metricDefinitions"][0]["definition"], "页面问号中的完整权威说明")
        self.assertEqual(provider.calls, 0)

    def test_reuse_executes_verified_contract(self) -> None:
        provider = Provider([ok()])
        result = query.query_metric(question="会员贡献最近7天复购率趋势图", catalog=catalog(), contracts=contracts(), provider=provider)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["bindingSource"], "template_reuse")
        self.assertEqual(result["presentation"]["mode"], "chart")
        self.assertEqual(provider.calls, 1)

    def test_reuse_drift_falls_back_once(self) -> None:
        provider = Provider([{"raise": "binding_drift"}, ok()])
        result = query.query_metric(question="会员贡献最近7天复购率", catalog=catalog(), contracts=contracts(), provider=provider)
        self.assertEqual(result["status"], "success")
        self.assertTrue(result["fallbackUsed"])
        self.assertEqual(provider.discoveries, 1)
        self.assertEqual(provider.calls, 2)
        self.assertEqual(provider.persisted, 1)

    def test_authorization_never_falls_back(self) -> None:
        provider = Provider([{"raise": "authorization"}])
        result = query.query_metric(question="会员贡献最近7天复购率", catalog=catalog(), contracts=contracts(), provider=provider)
        self.assertEqual(result["status"], "error")
        self.assertFalse(result["fallbackUsed"])
        self.assertEqual(provider.discoveries, 0)

    def test_dynamic_option_is_resolved_before_execute(self) -> None:
        provider = Provider([ok()])
        result = query.query_metric(question="会员贡献最近7天黄金会员复购率", catalog=catalog(), contracts=contracts(dynamic=True), provider=provider)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["resolvedParameters"]["memberGrade"], "黄金会员")
        self.assertEqual(provider.last_parameters["memberGrade"], "grade-1")

    def test_fixture_provider_resolves_dynamic_option(self) -> None:
        provider = query.FixtureProvider({"optionValues": {"member-grade": {"黄金会员": "grade-1"}}, "responses": [ok()]})
        result = query.query_metric(question="会员贡献最近7天黄金会员复购率", catalog=catalog(), contracts=contracts(dynamic=True), provider=provider)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["resolvedParameters"]["memberGrade"], "黄金会员")

    def test_operation_gate_blocks_provider(self) -> None:
        provider = Provider([ok()])
        result = query.query_metric(question="会员贡献最近7天复购率", catalog=catalog(), contracts=contracts("needs_revalidation"), provider=provider)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(provider.calls, 0)

    def test_metric_on_parent_routes_to_executable_child_and_scoped_operation(self) -> None:
        source = {
            "dashboards": [{
                "key": "crm.store_performance", "name": "门店业绩", "widgets": [
                    {"key": "crm.store_performance.overview", "title": "门店业绩", "executionStatus": "needs_revalidation",
                     "directOperationRefs": ["example.analytics.data_query"],
                     "metrics": [{"key": "turnover", "name": "营业额", "authoritativeDefinition": "销售实收减销售实退"}]},
                    {"key": "crm.store_performance.metric_trend", "title": "指标趋势", "aliases": ["营业额"],
                     "executionStatus": "executable", "semanticFingerprint": "sha256:semantic",
                     "directOperationRefs": ["example.analytics.data_query"], "metrics": []},
                ],
            }]
        }
        operation = {"operationId": "example.analytics.data_query.crm.store_performance", "executionStatus": "executable",
                     "schemaFingerprint": "sha256:schema", "responseMapping": {"rows": "rows"}}
        bindings = {"bindings": [{"dashboardTemplateKey": "crm.store_performance", "route": "/storeformance2/view",
                                   "widgetBindings": [{"widgetTemplateKey": "crm.store_performance.metric_trend", "widgetId": "w1", "datasetId": "d1"}]}]}
        provider = Provider([ok()])
        result = query.query_metric(question="查询本月营业额", catalog=source, contracts={"contracts": [operation]},
                                    bindings=bindings, provider=provider, output="summary")
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["selection"][0]["widgetKey"], "crm.store_performance.metric_trend")
        self.assertEqual(result["selection"][0]["metricKey"], "turnover")
        self.assertEqual(result["bindingSource"], "instance_cache")


if __name__ == "__main__":
    unittest.main()
